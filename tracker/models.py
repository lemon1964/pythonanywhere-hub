from django.db import models


class Counter(models.Model):
    event = models.CharField(max_length=120)
    src = models.CharField(max_length=120, blank=True, default="")
    count = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("event", "src")
        indexes = [
            models.Index(fields=["event", "src"]),
            models.Index(fields=["src"]),
        ]

    def __str__(self) -> str:
        return f"{self.src}:{self.event}={self.count}"
