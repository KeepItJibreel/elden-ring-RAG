from django.db import models

class Chunk(models.Model):
    name = models.CharField(max_length=255, default="")
    category = models.CharField(max_length=50, default="")
    source = models.CharField(max_length=255)
    text = models.TextField()
    embedding = models.JSONField()

    def __str__(self):
        return f"{self.category}: {self.name}"