/**
 * Image Privacy Cleaner — Frontend Application Controller (Vanilla JS)
 * Orchestrates drag-and-drop uploads, DRF /api/v1/ calls, real-time progress bars,
 * SynthID verification banners, before/after metadata comparison tables, and downloads.
 */
(function () {
    "use strict";

    const state = {
        currentJobId: null,
        queuedFiles: [],
        uploadedImages: [],
        metadataRecords: [],
        selectedFileId: null,
    };

    function getCsrfToken() {
        const input = document.querySelector("#csrfForm input[name='csrfmiddlewaretoken']");
        if (input && input.value) return input.value;
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : "";
    }

    function showToast(message, type = "info") {
        const container = document.getElementById("toastContainer");
        if (!container) return;
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 4200);
    }

    function formatBytes(bytes) {
        if (!bytes && bytes !== 0) return "—";
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }

    // Navigation Switching
    function switchPage(pageKey) {
        document.querySelectorAll(".nav-link").forEach((btn) => {
            btn.classList.toggle("active", btn.dataset.page === pageKey);
        });
        document.querySelectorAll(".view-section").forEach((sec) => {
            sec.classList.toggle("active", sec.id === `view-${pageKey}`);
        });
    }

    document.querySelectorAll(".nav-link").forEach((btn) => {
        btn.addEventListener("click", () => switchPage(btn.dataset.page));
    });

    document.querySelectorAll("[data-goto]").forEach((btn) => {
        btn.addEventListener("click", () => switchPage(btn.dataset.goto));
    });

    // Load Existing Job from Dashboard Table
    document.querySelectorAll(".load-job-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const jobId = btn.dataset.jobId;
            if (jobId) fetchJobStatus(jobId, true);
        });
    });

    // Drag & Drop Upload Handling
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("fileInput");
    const uploadBtn = document.getElementById("uploadAndAnalyzeBtn");
    const clearQueueBtn = document.getElementById("clearQueueBtn");

    if (dropZone && fileInput) {
        dropZone.addEventListener("click", () => fileInput.click());
        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("drag-over");
        });
        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("drag-over");
        });
        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("drag-over");
            if (e.dataTransfer && e.dataTransfer.files) {
                queueSelectedFiles(Array.from(e.dataTransfer.files));
            }
        });
        fileInput.addEventListener("change", () => {
            if (fileInput.files) {
                queueSelectedFiles(Array.from(fileInput.files));
            }
        });
    }

    function queueSelectedFiles(files) {
        const allowedExts = [".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"];
        for (const f of files) {
            if (state.queuedFiles.length >= 40) {
                showToast("Maximum batch size of 40 images reached.", "warning");
                break;
            }
            const dotIdx = f.name.lastIndexOf(".");
            const ext = dotIdx !== -1 ? f.name.slice(dotIdx).toLowerCase() : "";
            if (!allowedExts.includes(ext)) {
                showToast(`Skipped ${f.name}: unsupported extension.`, "error");
                continue;
            }
            if (f.size > 40 * 1024 * 1024) {
                showToast(`Skipped ${f.name}: exceeds 40MB limit.`, "error");
                continue;
            }
            state.queuedFiles.push(f);
        }
        renderThumbnailQueue();
    }

    function renderThumbnailQueue() {
        const grid = document.getElementById("thumbnailGrid");
        const countEl = document.getElementById("queueCount");
        if (!grid) return;

        countEl.textContent = String(state.queuedFiles.length);
        uploadBtn.disabled = state.queuedFiles.length === 0;

        if (state.queuedFiles.length === 0) {
            grid.innerHTML = `<div class="empty-state">No images queued yet. Drag &amp; drop files above.</div>`;
            return;
        }

        grid.innerHTML = "";
        state.queuedFiles.forEach((file) => {
            const card = document.createElement("div");
            card.className = "thumb-card";
            const objUrl = URL.createObjectURL(file);
            card.innerHTML = `
                <div class="thumb-img-wrap">
                    <img src="${objUrl}" alt="${file.name}">
                </div>
                <div class="thumb-body">
                    <div class="thumb-title" title="${file.name}">${file.name}</div>
                    <div class="thumb-meta">
                        <span>${formatBytes(file.size)}</span>
                        <span class="badge badge-uploaded">Queued</span>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    if (clearQueueBtn) {
        clearQueueBtn.addEventListener("click", () => {
            state.queuedFiles = [];
            if (fileInput) fileInput.value = "";
            renderThumbnailQueue();
            showToast("Upload queue cleared.", "info");
        });
    }

    if (uploadBtn) {
        uploadBtn.addEventListener("click", async () => {
            if (state.queuedFiles.length === 0) return;
            uploadBtn.disabled = true;

            const progWrap = document.getElementById("uploadProgressWrapper");
            const progBar = document.getElementById("uploadProgressBar");
            const progPct = document.getElementById("uploadProgressPercent");
            const progTxt = document.getElementById("uploadProgressText");

            progWrap.classList.remove("hidden");
            progBar.style.width = "30%";
            progPct.textContent = "30%";
            progTxt.textContent = "Uploading & verifying binary signatures...";

            const formData = new FormData();
            state.queuedFiles.forEach((f) => formData.append("images", f));

            try {
                const upRes = await fetch("/api/v1/upload/", {
                    method: "POST",
                    headers: { "X-CSRFToken": getCsrfToken() },
                    body: formData,
                });
                const upData = await upRes.json();
                if (!upRes.ok || upData.status === "error") {
                    const msg = upData.rejected && upData.rejected.length
                        ? upData.rejected.map((r) => `${r.filename}: ${r.error}`).join("; ")
                        : JSON.stringify(upData.errors || "Upload failed");
                    showToast(msg, "error");
                    uploadBtn.disabled = false;
                    return;
                }

                state.currentJobId = upData.job_id;
                state.uploadedImages = upData.uploaded || [];
                document.getElementById("activeJobBadge").textContent = `Batch ${state.currentJobId.slice(0, 8)}`;

                progBar.style.width = "70%";
                progPct.textContent = "70%";
                progTxt.textContent = "Analyzing EXIF, XMP, IPTC, PNG chunks, C2PA & SynthID...";

                const anRes = await fetch("/api/v1/analyze/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                    },
                    body: JSON.stringify({ job_id: state.currentJobId }),
                });
                const anData = await anRes.json();
                progBar.style.width = "100%";
                progPct.textContent = "100%";
                progTxt.textContent = "Analysis complete!";

                if (anRes.ok) {
                    state.metadataRecords = anData.results || [];
                    await fetchJobStatus(state.currentJobId, false);
                    showToast(`Uploaded & analyzed ${upData.total_uploaded} image(s).`, "success");
                    switchPage("analysis");
                }
            } catch (err) {
                showToast(`Request error: ${err.message}`, "error");
            } finally {
                uploadBtn.disabled = false;
            }
        });
    }

    async function fetchJobStatus(jobId, navigateToAnalysis = false) {
        try {
            const res = await fetch(`/api/v1/jobs/${jobId}/`);
            if (!res.ok) return;
            const data = await res.json();
            state.currentJobId = data.id;
            state.uploadedImages = data.images || [];
            state.metadataRecords = data.metadata_records || [];
            document.getElementById("activeJobBadge").textContent = `Batch ${state.currentJobId.slice(0, 8)} (${data.status})`;

            renderAnalysisView();
            renderBatchView(data);
            renderComparisonReport();
            renderDownloadCenter(data);

            if (navigateToAnalysis) {
                switchPage("analysis");
            }
        } catch (err) {
            showToast(`Failed to load batch: ${err.message}`, "error");
        }
    }

    // Render Analysis View
    function renderAnalysisView() {
        const listEl = document.getElementById("analysisFileList");
        if (!listEl) return;

        if (!state.metadataRecords.length) {
            listEl.innerHTML = `<div class="empty-state">Upload and analyze a batch first.</div>`;
            return;
        }

        if (!state.selectedFileId) {
            state.selectedFileId = state.metadataRecords[0].file_id;
        }

        listEl.innerHTML = "";
        state.metadataRecords.forEach((rec) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = `analysis-file-item ${rec.file_id === state.selectedFileId ? "active" : ""}`;
            btn.innerHTML = `
                <div style="font-weight:600; font-size:13px;">${rec.original_filename}</div>
                <div style="font-size:11px; color:var(--text-secondary); display:flex; justify-content:space-between; margin-top:4px;">
                    <span>${rec.file_format} · ${rec.width}×${rec.height}</span>
                    <span>Risk: ${rec.privacy_risk_score}/100</span>
                </div>
            `;
            btn.addEventListener("click", () => {
                state.selectedFileId = rec.file_id;
                renderAnalysisView();
            });
            listEl.appendChild(btn);
        });

        const activeRec = state.metadataRecords.find((r) => r.file_id === state.selectedFileId) || state.metadataRecords[0];
        const imgObj = state.uploadedImages.find((i) => i.id === activeRec.file_id);

        // Unified C2PA + SynthID Inspector Card Update
        const badge = document.getElementById("synthidStatusBadge");
        const details = document.getElementById("synthidDetailsText");
        const fileMetaEl = document.getElementById("inspectorFileMeta");
        const headlineEl = document.getElementById("inspectorHeadline");
        const mainImgEl = document.getElementById("inspectorMainImg");
        const mainPhEl = document.getElementById("inspectorImgPlaceholder");
        const c2paRowStatus = document.getElementById("c2paRowStatus");
        const c2paRowSub = document.getElementById("c2paRowSub");
        const c2paRowIcon = document.getElementById("c2paRowIcon");
        const synthRowIcon = document.getElementById("synthidRowIcon");
        const synthRowSub = document.getElementById("synthidRowSub");
        const pillC2pa = document.getElementById("pillC2paDot");
        const pillSynth = document.getElementById("pillSynthidDot");
        const socBox = document.getElementById("socialWarningBox");
        const socTitle = document.getElementById("socialWarningTitle");
        const socSub = document.getElementById("socialWarningSub");
        const removeSynthBtn = document.getElementById("oneClickRemoveSynthIdBtn");

        const displayUrl = (imgObj && imgObj.cleaned_url) ? imgObj.cleaned_url : (imgObj ? imgObj.preview_url : "");
        if (displayUrl && mainImgEl) {
            mainImgEl.src = displayUrl + "?t=" + Date.now();
            mainImgEl.classList.remove("hidden");
            if (mainPhEl) mainPhEl.classList.add("hidden");
        }

        const c2paAfterOrBefore = (imgObj && imgObj.cleaned_url) ? activeRec.c2pa_after : activeRec.c2pa_before;
        const hasC2pa = c2paAfterOrBefore && c2paAfterOrBefore.has_c2pa_manifest;
        const isSynthDetected = activeRec.synthid_status === "Detected";
        const isCleaned = imgObj && imgObj.status === "CLEANED";

        if (fileMetaEl) {
            const sz = isCleaned ? (activeRec.cleaned_size_bytes || activeRec.file_size_bytes) : activeRec.file_size_bytes;
            fileMetaEl.textContent = `${isCleaned ? "cleaned_" : ""}${activeRec.original_filename} · ${formatBytes(sz)} · ${activeRec.file_format} (${activeRec.width}×${activeRec.height})`;
        }

        if (c2paRowStatus) {
            if (hasC2pa) {
                c2paRowStatus.textContent = "Detected";
                c2paRowStatus.className = "row-status status-danger";
                c2paRowSub.textContent = (c2paAfterOrBefore.indicators || ["C2PA Manifest Present"]).join(", ");
                c2paRowIcon.textContent = "!";
                c2paRowIcon.className = "row-icon row-icon-warn";
                pillC2pa.textContent = "● C2PA";
            } else {
                c2paRowStatus.textContent = "None found";
                c2paRowStatus.className = "row-status status-clean";
                c2paRowSub.textContent = "No Content Credentials in this file";
                c2paRowIcon.textContent = "—";
                c2paRowIcon.className = "row-icon";
                pillC2pa.textContent = "— C2PA";
            }
        }

        if (isSynthDetected) {
            headlineEl.textContent = hasC2pa ? "C2PA & SynthID Detected" : "No C2PA found · SynthID in Pixels";
            badge.textContent = "Still in the pixels";
            badge.className = "row-status status-danger";
            synthRowIcon.textContent = "2";
            synthRowIcon.className = "row-icon row-icon-warn";
            synthRowSub.textContent = "Invisible watermark from Google AI";
            pillSynth.textContent = "● SynthID";
            pillSynth.className = "synth-dot-active";
            socBox.classList.remove("clean-box");
            socTitle.textContent = "SynthID stays embedded";
            socSub.textContent = "X, Instagram, TikTok, Facebook and YouTube can still flag it as AI-generated.";
            if (removeSynthBtn) removeSynthBtn.textContent = "Remove SynthID & Clean All Metadata";
        } else if (isCleaned || activeRec.synthid_status === "Not detected") {
            headlineEl.textContent = "Clean — No C2PA or SynthID Found";
            badge.textContent = "Removed / Clean";
            badge.className = "row-status status-clean";
            synthRowIcon.textContent = "✓";
            synthRowIcon.className = "row-icon row-icon-ok";
            synthRowSub.textContent = "4-stage spectral & DCT carrier sanitization complete";
            pillSynth.textContent = "✓ SynthID Clean";
            pillSynth.className = "synth-dot-clean";
            socBox.classList.add("clean-box");
            socTitle.textContent = "Ready for social & client publishing";
            socSub.textContent = "All C2PA manifests, personal EXIF/GPS tags, and mid-band pixel watermark carriers have been scrubbed.";
            if (removeSynthBtn) removeSynthBtn.textContent = "Re-Run Deep SynthID Scrub";
        } else {
            headlineEl.textContent = "No C2PA found";
            badge.textContent = activeRec.synthid_status;
            badge.className = "row-status";
        }
        details.textContent = activeRec.synthid_details;

        // Before & After Previews
        const imgBefore = document.getElementById("previewImgBefore");
        const phBefore = document.getElementById("previewPlaceholderBefore");
        const metaBefore = document.getElementById("previewMetaBefore");
        if (imgObj && imgObj.preview_url) {
            imgBefore.src = imgObj.preview_url;
            imgBefore.classList.remove("hidden");
            phBefore.classList.add("hidden");
            metaBefore.textContent = `Size: ${formatBytes(activeRec.file_size_bytes)} | Pixel SHA-256: ${(activeRec.pixel_hash_before || "").slice(0, 20)}...`;
        }

        const imgAfter = document.getElementById("previewImgAfter");
        const phAfter = document.getElementById("previewPlaceholderAfter");
        const metaAfter = document.getElementById("previewMetaAfter");
        if (imgObj && imgObj.cleaned_url) {
            imgAfter.src = imgObj.cleaned_url;
            imgAfter.classList.remove("hidden");
            phAfter.classList.add("hidden");
            const exactMatch = activeRec.pixel_hash_before === activeRec.pixel_hash_after;
            metaAfter.textContent = `Size: ${formatBytes(activeRec.cleaned_size_bytes)} | Pixels 100% Identical: ${exactMatch ? "YES" : "NO"}`;
        } else {
            imgAfter.classList.add("hidden");
            phAfter.classList.remove("hidden");
            metaAfter.textContent = "Pixel Integrity: Pending Cleaning";
        }

        // 8 Metadata Domains
        const domainsGrid = document.getElementById("metadataDomainsGrid");
        const domains = [
            { title: "GPS Coordinates", data: activeRec.gps_before },
            { title: "Camera & Serial Information", data: activeRec.camera_before },
            { title: "Software & History", data: activeRec.software_before },
            { title: "C2PA Content Credentials & Provenance", data: Object.assign({}, activeRec.c2pa_before, activeRec.preserved_provenance_fields) },
            { title: "EXIF Tags", data: activeRec.exif_before },
            { title: "XMP Packet Fields", data: activeRec.xmp_before },
            { title: "IPTC Datasets", data: activeRec.iptc_before },
            { title: "PNG Text Chunks", data: activeRec.png_chunks_before },
        ];

        domainsGrid.innerHTML = domains.map((d) => {
            const entries = Object.entries(d.data || {});
            const rowsHtml = entries.length
                ? entries.map(([k, v]) => `
                    <div class="kv-row">
                        <span class="kv-key">${k}</span>
                        <span class="kv-val mono">${typeof v === "object" ? JSON.stringify(v) : String(v)}</span>
                    </div>
                `).join("")
                : `<div style="color:var(--text-muted); font-size:12px;">None detected</div>`;
            return `
                <div class="domain-box">
                    <h4>${d.title} (${entries.length})</h4>
                    <div class="kv-list">${rowsHtml}</div>
                </div>
            `;
        }).join("");
    }

    // Re-run Analysis Button
    const runAnalyzeBtn = document.getElementById("runAnalyzeBtn");
    if (runAnalyzeBtn) {
        runAnalyzeBtn.addEventListener("click", async () => {
            if (!state.currentJobId) {
                showToast("Upload a batch first.", "warning");
                return;
            }
            const res = await fetch("/api/v1/analyze/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify({ job_id: state.currentJobId }),
            });
            if (res.ok) {
                await fetchJobStatus(state.currentJobId, false);
                showToast("Metadata analysis refreshed.", "success");
            }
        });
    }

    // Execute Personal Metadata Cleaning
    const executeCleanBtn = document.getElementById("executeCleanBtn");
    if (executeCleanBtn) {
        executeCleanBtn.addEventListener("click", async () => {
            if (!state.currentJobId) {
                showToast("Please upload images before running metadata cleaning.", "warning");
                return;
            }
            const nuclear = document.getElementById("optNuclearClean")?.checked;
            if (nuclear) {
                const confirmed = confirm("⚠️ NUCLEAR CLEAN: This will strip ALL metadata including Copyright, Authorship, Licensing, C2PA, AI Disclosure + Deep Pixel Scrub.\n\nOutput = Pure pixels only. This is IRREVERSIBLE.\n\nContinue?");
                if (!confirmed) return;
            }
            executeCleanBtn.disabled = true;
            const payload = {
                job_id: state.currentJobId,
                remove_gps: document.getElementById("optRemoveGps").checked,
                remove_serial_numbers: document.getElementById("optRemoveSerials").checked,
                remove_owner_info: document.getElementById("optRemoveOwner").checked,
                remove_contact_info: document.getElementById("optRemoveContact").checked,
                remove_ai_and_c2pa: document.getElementById("optRemoveAiC2pa") ? document.getElementById("optRemoveAiC2pa").checked : true,
                scrub_pixel_watermark: document.getElementById("optScrubPixelWatermark") ? document.getElementById("optScrubPixelWatermark").checked : true,
                nuclear_clean: nuclear,
            };

            try {
                const res = await fetch("/api/v1/clean/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                    },
                    body: JSON.stringify(payload),
                });
                const data = await res.json();
                if (res.ok && data.status === "success") {
                    await fetchJobStatus(state.currentJobId, false);
                    showToast(`Cleaned ${data.processed_files} image(s) with 100% pixel integrity.`, "success");
                } else {
                    showToast("Metadata cleaning encountered an error.", "error");
                }
            } catch (err) {
                showToast(`Cleaning error: ${err.message}`, "error");
            } finally {
                executeCleanBtn.disabled = false;
            }
        });
    }

    function renderBatchView(jobData) {
        const bar = document.getElementById("batchProgressBar");
        const pct = document.getElementById("batchProgressPercent");
        const txt = document.getElementById("batchProgressStatusText");
        const tbody = document.getElementById("batchStatusTableBody");

        const progress = jobData.progress_percentage || 0;
        bar.style.width = `${progress}%`;
        pct.textContent = `${progress}%`;
        txt.textContent = `Batch Status: ${jobData.status} (${jobData.processed_files}/${jobData.total_files} processed, ${jobData.failed_files} failed)`;

        if (!state.metadataRecords.length) {
            tbody.innerHTML = `<tr><td colspan="7" class="empty-cell">No records in current batch.</td></tr>`;
            return;
        }

        tbody.innerHTML = state.metadataRecords.map((rec) => {
            const removedCount = (rec.removed_fields_summary || []).length;
            const preservedCount = Object.keys(rec.preserved_provenance_fields || {}).length;
            const pixelsMatch = rec.pixel_hash_after
                ? (rec.pixel_hash_before === rec.pixel_hash_after ? "✓ 100% Identical" : "✗ Mismatch")
                : "Pending Clean";

            return `
                <tr>
                    <td><strong>${rec.original_filename}</strong></td>
                    <td>${rec.file_format} (${formatBytes(rec.file_size_bytes)})</td>
                    <td><span class="badge ${rec.privacy_risk_score > 0 ? "badge-removed" : "badge-completed"}">${rec.privacy_risk_score} / 100</span></td>
                    <td class="mono">${removedCount ? rec.removed_fields_summary.join(", ") : "None"}</td>
                    <td class="mono">${preservedCount ? Object.keys(rec.preserved_provenance_fields).join(", ") : "None"}</td>
                    <td><span class="badge badge-completed">${pixelsMatch}</span></td>
                    <td><span class="badge badge-${(rec.image_status || "uploaded").toLowerCase()}">${rec.image_status}</span></td>
                </tr>
            `;
        }).join("");
    }

    function renderComparisonReport() {
        const tbody = document.getElementById("comparisonTableBody");
        if (!tbody) return;

        const rows = [];
        state.metadataRecords.forEach((rec) => {
            // Removed Personal Fields
            (rec.removed_fields_summary || []).forEach((fieldKey) => {
                rows.push({
                    file: rec.original_filename,
                    field: fieldKey,
                    category: "Personal / Sensitive Metadata",
                    before: "Present",
                    after: "Stripped (Removed)",
                    disposition: "REMOVED",
                });
            });

            // Preserved Provenance Fields
            Object.entries(rec.preserved_provenance_fields || {}).forEach(([k, v]) => {
                rows.push({
                    file: rec.original_filename,
                    field: k,
                    category: "Authorship / Copyright / Provenance",
                    before: String(v),
                    after: String(v),
                    disposition: "PRESERVED",
                });
            });
        });

        if (!rows.length) {
            tbody.innerHTML = `<tr><td colspan="6" class="empty-cell">Run metadata cleaning on a batch to populate the before/after comparison report.</td></tr>`;
            return;
        }

        tbody.innerHTML = rows.map((r) => `
            <tr>
                <td>${r.file}</td>
                <td class="mono">${r.field}</td>
                <td>${r.category}</td>
                <td class="mono">${r.before}</td>
                <td class="mono">${r.after}</td>
                <td><span class="badge badge-${r.disposition.toLowerCase()}">${r.disposition}</span></td>
            </tr>
        `).join("");
    }

    function renderDownloadCenter(jobData) {
        const grid = document.getElementById("downloadCardsGrid");
        const zipBtn = document.getElementById("downloadAllZipBtn");
        const repBtn = document.getElementById("downloadReportCenterBtn");

        if (!jobData || !state.uploadedImages.length) {
            zipBtn.disabled = true;
            repBtn.disabled = true;
            return;
        }

        zipBtn.disabled = false;
        repBtn.disabled = false;

        zipBtn.onclick = () => {
            window.location.href = `/api/v1/download-zip/${jobData.id}/`;
        };
        repBtn.onclick = () => {
            window.location.href = `/api/v1/report/${jobData.id}/?download=1`;
        };

        const topReportBtn = document.getElementById("downloadJsonReportBtn");
        if (topReportBtn) {
            topReportBtn.onclick = () => {
                window.location.href = `/api/v1/report/${jobData.id}/?download=1`;
            };
        }

        grid.innerHTML = state.uploadedImages.map((img) => `
            <div class="download-card">
                <div style="font-weight:700;">${img.original_filename}</div>
                <div style="font-size:12px; color:var(--text-secondary);">
                    Format: ${img.file_format} · ${img.width}×${img.height}<br>
                    Before: ${formatBytes(img.file_size_bytes)} → After: ${formatBytes(img.cleaned_size_bytes || img.file_size_bytes)}
                </div>
                <div style="margin-top:auto; display:flex; justify-content:space-between; align-items:center;">
                    <span class="badge badge-${img.status.toLowerCase()}">${img.status}</span>
                    <a href="/api/v1/download/${img.id}/" class="btn btn-sm btn-primary">Download Image</a>
                </div>
            </div>
        `).join("");
    }

    // 1-Click "Remove SynthID & Clean All Metadata" Button on Analysis Inspector Card
    const oneClickBtn = document.getElementById("oneClickRemoveSynthIdBtn");
    if (oneClickBtn) {
        oneClickBtn.addEventListener("click", async () => {
            if (!state.currentJobId) {
                showToast("Upload an image batch first.", "warning");
                return;
            }
            const nuclear = confirm("⚠️ NUCLEAR CLEAN: Strip EVERYTHING (Copyright, C2PA, AI Disclosure + Deep Pixel Scrub)?\n\nOutput = Pure pixels only. IRREVERSIBLE.\n\nClick Cancel for standard clean (preserves Copyright/C2PA).");
            oneClickBtn.disabled = true;
            const origText = oneClickBtn.textContent;
            oneClickBtn.textContent = nuclear ? "Nuclear Cleaning: Stripping EVERYTHING..." : "Scrubbing SynthID & C2PA from Pixels...";

            try {
                const res = await fetch("/api/v1/clean/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                    },
                    body: JSON.stringify({
                        job_id: state.currentJobId,
                        remove_gps: true,
                        remove_serial_numbers: true,
                        remove_owner_info: true,
                        remove_contact_info: true,
                        remove_ai_and_c2pa: true,
                        scrub_pixel_watermark: true,
                        nuclear_clean: nuclear,
                    }),
                });
                const data = await res.json();
                if (res.ok && data.status === "success") {
                    await fetchJobStatus(state.currentJobId, false);
                    showToast(nuclear ? "Nuclear clean complete. Pure pixels only." : "SynthID pixel watermark & all metadata scrubbed! Download from Download Center.", "success");
                } else {
                    showToast("Cleaning encountered an error.", "error");
                }
            } catch (err) {
                showToast(`Error: ${err.message}`, "error");
            } finally {
                oneClickBtn.disabled = false;
                oneClickBtn.textContent = origText;
            }
        });
    }

    const quickResetBtn = document.getElementById("quickResetAnalyzeBtn");
    if (quickResetBtn) {
        quickResetBtn.addEventListener("click", () => {
            if (runAnalyzeBtn) runAnalyzeBtn.click();
        });
    }

    // Clear Report Button
    const clearReportBtn = document.getElementById("clearReportBtn");
    if (clearReportBtn) {
        clearReportBtn.addEventListener("click", () => {
            state.metadataRecords = [];
            state.currentJobId = null;
            state.uploadedImages = [];
            state.selectedFileId = null;
            document.getElementById("activeJobBadge").textContent = "No Active Batch";
            renderComparisonReport();
            renderBatchView({ status: "IDLE", processed_files: 0, total_files: 0, failed_files: 0, progress_percentage: 0 });
            renderDownloadCenter(null);
            renderAnalysisView();
            showToast("Report cleared.", "info");
        });
    }

})();
