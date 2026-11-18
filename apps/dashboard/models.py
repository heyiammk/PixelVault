"""
Dashboard app does not store separate domain models; it aggregates telemetry
from BatchJob, ImageFile, MetadataRecord, and CleaningLog.
"""
from django.db import models
