from django.core.management.base import BaseCommand, CommandError
from apps.batch_processor.models import BatchJob
from apps.batch_processor.services import run_batch_analysis, run_batch_cleaning, cleanup_expired_temp_files


class Command(BaseCommand):
    help = "Process a BatchJob (analyze and clean) or clean up expired temporary files."

    def add_arguments(self, parser):
        parser.add_argument("--job-id", type=str, help="UUID of the BatchJob to analyze and clean.")
        parser.add_argument(
            "--cleanup-temp",
            action="store_true",
            help="Delete expired files in media/temp/ based on TEMP_FILE_RETENTION_HOURS.",
        )

    def handle(self, *args, **options):
        if options.get("cleanup_temp"):
            deleted = cleanup_expired_temp_files()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired temporary file(s)."))

        job_id = options.get("job_id")
        if job_id:
            try:
                job = BatchJob.objects.get(id=job_id)
            except BatchJob.DoesNotExist as exc:
                raise CommandError(f"BatchJob {job_id} does not exist.") from exc

            self.stdout.write(f"Analyzing BatchJob {job.id}...")
            run_batch_analysis(job)
            self.stdout.write(f"Cleaning BatchJob {job.id}...")
            run_batch_cleaning(job, options=job.cleaning_options or None)
            self.stdout.write(self.style.SUCCESS(f"BatchJob {job.id} completed with status {job.status}."))
