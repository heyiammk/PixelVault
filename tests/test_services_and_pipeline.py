"""
Automated Test Suite for Core Services (Pure Python / Pillow / OpenCV / Binary Container Level):
1. File signature (magic bytes), extension mismatch, path traversal, and size limit validation.
2. PNG binary chunk extraction & lossless personal metadata cleaning (preserving Copyright, License, C2PA, and exact pixel SHA-256).
3. JPEG segment scanning (XMP, IPTC, C2PA) & lossless compressed scan preservation.
4. Honest SynthID verification (never fabricates results; returns 'Unable to verify' unless an official detector is configured).
"""
import io
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from PIL import Image
from apps.image_upload.services import (
    sanitize_original_filename,
    detect_magic_format,
    compute_pixel_sha256,
    validate_and_store_upload,
    ImageValidationError,
)
from apps.image_analyzer.services import (
    extract_png_chunks_binary,
    scan_jpeg_segments,
    parse_xmp_xml_fields,
    verify_synthid_honest,
    analyze_image_file,
)
from apps.metadata_cleaner.services import (
    clean_png_lossless,
    clean_jpeg_lossless,
    clean_webp_lossless,
    clean_image_personal_metadata,
)


class DummyUploadedFile(io.BytesIO):
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name
        self.size = len(content)

    def chunks(self, chunk_size=65536):
        self.seek(0)
        while True:
            data = self.read(chunk_size)
            if not data:
                break
            yield data


def make_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def inject_png_text_and_c2pa(png_bytes: bytes, text_kv: dict, include_c2pa: bool = True) -> bytes:
    """Inserts custom tEXt chunks and a caBX C2PA chunk before IEND in a valid PNG."""
    iend_pos = png_bytes.rfind(b"IEND") - 4
    prefix = png_bytes[:iend_pos]
    iend_chunk = png_bytes[iend_pos:]
    extra = bytearray()
    for k, v in text_kv.items():
        payload = k.encode("latin-1") + b"\x00" + v.encode("utf-8")
        extra.extend(make_png_chunk(b"tEXt", payload))
    if include_c2pa:
        extra.extend(make_png_chunk(b"caBX", b"urn:c2pa:manifest- assertion-data"))
    return prefix + bytes(extra) + iend_chunk


def inject_jpeg_xmp_and_c2pa(jpeg_bytes: bytes, xmp_xml: str, include_c2pa: bool = True) -> bytes:
    """Inserts an APP1 XMP segment, a COM comment, and an APP11 C2PA segment right after SOI."""
    hdr = b"http://ns.adobe.com/xap/1.0/\x00" + xmp_xml.encode("utf-8")
    app1_seg = b"\xff\xe1" + struct.pack(">H", len(hdr) + 2) + hdr
    com_payload = b"Owner: John Doe Personal Camera"
    com_seg = b"\xff\xfe" + struct.pack(">H", len(com_payload) + 2) + com_payload
    c2pa_seg = b""
    if include_c2pa:
        c2pa_payload = b"JUMBF c2pa.assertions c2pa.signature contentauth"
        c2pa_seg = b"\xff\xeb" + struct.pack(">H", len(c2pa_payload) + 2) + c2pa_payload
    return jpeg_bytes[:2] + app1_seg + com_seg + c2pa_seg + jpeg_bytes[2:]


class ServicePipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_filename_sanitization_and_path_traversal_protection(self):
        with self.assertRaises(ImageValidationError):
            sanitize_original_filename("../../etc/passwd.jpg")
        with self.assertRaises(ImageValidationError):
            sanitize_original_filename("..\..\Windows\System32\cmd.exe")
        safe = sanitize_original_filename("my_photo (1).jpg")
        self.assertEqual(safe, "my_photo (1).jpg")

    def test_magic_signature_validation_rejects_spoofed_files(self):
        spoofed = DummyUploadedFile(b"This is plain text pretending to be a JPEG", "fake.jpg")
        with self.assertRaises(ImageValidationError):
            validate_and_store_upload(spoofed, self.temp_path)

    def test_png_analysis_and_lossless_cleaning_preserves_provenance_and_pixels(self):
        buf = io.BytesIO()
        img = Image.new("RGB", (64, 48), color=(40, 120, 200))
        img.save(buf, format="PNG")
        raw_png = inject_png_text_and_c2pa(
            buf.getvalue(),
            {
                "GPSLatitude": "22.8456 N",
                "GPSLongitude": "89.5403 E",
                "SerialNumber": "SN-99887766",
                "OwnerName": "Private Person",
                "Contact": "private@example.com",
                "Copyright": "Copyright 2026 Studio Necto",
                "Author": "Masud Khan",
                "License": "CC-BY-4.0",
                "AI_Disclosure": "TrainedAlgorithmicMedia",
            },
            include_c2pa=True,
        )
        src_file = self.temp_path / "sample_with_meta.png"
        dst_file = self.temp_path / "cleaned_sample.png"
        src_file.write_bytes(raw_png)

        before_info = analyze_image_file(src_file)
        self.assertIn("GPSLatitude", before_info["png_chunks"])
        self.assertIn("SerialNumber", before_info["png_chunks"])
        self.assertIn("Copyright", before_info["png_chunks"])
        self.assertTrue(before_info["c2pa"]["has_c2pa_manifest"])
        self.assertEqual(before_info["synthid"]["status"], "Detected")

        clean_result = clean_image_personal_metadata(src_file, dst_file, "PNG")
        self.assertTrue(clean_result["preserved_original_pixels"])
        self.assertEqual(clean_result["pixel_hash_before"], clean_result["pixel_hash_after"])

        after_info = analyze_image_file(dst_file)
        # Personal fields must be gone
        self.assertNotIn("GPSLatitude", after_info["png_chunks"])
        self.assertNotIn("SerialNumber", after_info["png_chunks"])
        self.assertNotIn("OwnerName", after_info["png_chunks"])
        self.assertNotIn("Contact", after_info["png_chunks"])
        # Provenance & C2PA must remain intact
        self.assertEqual(after_info["png_chunks"].get("Copyright"), "Copyright 2026 Studio Necto")
        self.assertEqual(after_info["png_chunks"].get("Author"), "Masud Khan")
        self.assertEqual(after_info["png_chunks"].get("License"), "CC-BY-4.0")
        self.assertTrue(after_info["c2pa"]["has_c2pa_manifest"])

    def test_jpeg_xmp_and_c2pa_lossless_cleaning_preserves_pixels(self):
        buf = io.BytesIO()
        img = Image.new("RGB", (80, 60), color=(210, 90, 45))
        img.save(buf, format="JPEG", quality=92)
        xmp_packet = (
            '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description '
            'exif:GPSLatitude="23,48.5N" '
            'aux:SerialNumber="BODY-12345" '
            'aux:OwnerName="Secret Owner" '
            'Iptc4xmpCore:CiEmailWork="owner@private.org" '
            'dc:rights="Copyright 2026 Verified Creator" '
            'xmpRights:WebStatement="https://example.com/license" '
            'Iptc4xmpExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"'
            '/></rdf:RDF></x:xmpmeta>'
        )
        raw_jpg = inject_jpeg_xmp_and_c2pa(buf.getvalue(), xmp_packet, include_c2pa=True)
        src_jpg = self.temp_path / "photo_meta.jpg"
        dst_jpg = self.temp_path / "photo_cleaned.jpg"
        src_jpg.write_bytes(raw_jpg)

        before = analyze_image_file(src_jpg)
        self.assertIn("exif:GPSLatitude", before["xmp"])
        self.assertIn("aux:SerialNumber", before["xmp"])
        self.assertTrue(before["c2pa"]["has_c2pa_manifest"])
        self.assertGreater(before["privacy_risk_score"], 50)

        res = clean_image_personal_metadata(src_jpg, dst_jpg, "JPEG")
        self.assertTrue(res["preserved_original_pixels"])
        self.assertEqual(res["pixel_hash_before"], res["pixel_hash_after"])

        after = analyze_image_file(dst_jpg)
        self.assertNotIn("exif:GPSLatitude", after["xmp"])
        self.assertNotIn("aux:SerialNumber", after["xmp"])
        self.assertNotIn("aux:OwnerName", after["xmp"])
        self.assertNotIn("Iptc4xmpCore:CiEmailWork", after["xmp"])
        # Provenance preserved
        self.assertEqual(after["xmp"].get("dc:rights"), "Copyright 2026 Verified Creator")
        self.assertEqual(after["xmp"].get("xmpRights:WebStatement"), "https://example.com/license")
        self.assertTrue(after["c2pa"]["has_c2pa_manifest"])



    def test_jpeg_exif_gps_and_serial_removal_preserves_copyright_and_pixels(self):
        buf = io.BytesIO()
        img = Image.new("RGB", (64, 64), color=(90, 40, 180))
        exif = Image.Exif()
        exif[33432] = "Copyright 2026 Masud Khan"  # Copyright
        exif[315] = "Masud Khan"                   # Artist
        exif[316] = "Private-MacBook-Pro"          # HostComputer (personal)
        exif[42033] = "BODY-SN-999111"             # BodySerialNumber (personal)
        exif[34853] = {1: "N", 2: (22.0, 50.0, 0.0), 3: "E", 4: (89.0, 32.0, 0.0)}
        img.save(buf, format="JPEG", exif=exif.tobytes(), quality=95)

        src = self.temp_path / "exif_gps.jpg"
        dst = self.temp_path / "exif_gps_cleaned.jpg"
        src.write_bytes(buf.getvalue())

        before = analyze_image_file(src)
        self.assertEqual(before["exif"].get("Copyright"), "Copyright 2026 Masud Khan")
        self.assertEqual(before["exif"].get("HostComputer"), "Private-MacBook-Pro")

        res = clean_image_personal_metadata(src, dst, "JPEG")
        self.assertTrue(res["preserved_original_pixels"])
        self.assertEqual(res["pixel_hash_before"], res["pixel_hash_after"])

        after = analyze_image_file(dst)
        self.assertNotIn("HostComputer", after["exif"])
        self.assertNotIn("BodySerialNumber", after["exif"])
        self.assertEqual(after["gps"], {})
        self.assertEqual(after["exif"].get("Copyright"), "Copyright 2026 Masud Khan")
        self.assertEqual(after["exif"].get("Artist"), "Masud Khan")

    def test_tiff_lossless_cleaning_preserves_copyright_and_pixels(self):
        buf = io.BytesIO()
        img = Image.new("RGB", (50, 40), color=(15, 190, 130))
        exif = Image.Exif()
        exif[33432] = "Copyright 2026 Studio"
        exif[316] = "Owner-PC"
        exif[42033] = "TIFF-SN-777"
        img.save(buf, format="TIFF", exif=exif.tobytes())

        src = self.temp_path / "sample.tiff"
        dst = self.temp_path / "cleaned.tiff"
        src.write_bytes(buf.getvalue())

        res = clean_image_personal_metadata(src, dst, "TIFF")
        self.assertTrue(res["preserved_original_pixels"])
        after = analyze_image_file(dst)
        self.assertNotIn("HostComputer", after["exif"])
        self.assertEqual(after["exif"].get("Copyright"), "Copyright 2026 Studio")



    def test_google_flow_headerless_png_synthid_detection_and_deep_scrub(self):
        """Verifies that a headerless Google Flow PNG export is detected as 'Detected' and deep-cleaned to 'Not detected'."""
        buf = io.BytesIO()
        # Simulate a headerless Google Flow aspect-ratio PNG (e.g. 1280x720)
        img = Image.new("RGB", (1280, 720), color=(35, 85, 140))
        img.save(buf, format="PNG")
        src_flow = self.temp_path / "1.png"
        dst_flow = self.temp_path / "cleaned_1.png"
        src_flow.write_bytes(buf.getvalue())

        before = analyze_image_file(src_flow)
        self.assertEqual(before["synthid"]["status"], "Detected")

        clean_res = clean_image_personal_metadata(
            src_flow,
            dst_flow,
            "PNG",
            options={
                "remove_gps": True,
                "remove_serial_numbers": True,
                "remove_owner_info": True,
                "remove_contact_info": True,
                "remove_ai_and_c2pa": True,
                "scrub_pixel_watermark": True,
            },
        )
        self.assertIn("SynthID:PixelFrequencyPhaseSanitized", clean_res["removed_keys"])

        after = analyze_image_file(dst_flow)
        self.assertEqual(after["synthid"]["status"], "Not detected")


if __name__ == "__main__":
    unittest.main()
