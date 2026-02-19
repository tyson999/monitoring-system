from django.db import models

class URLCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class MonitoredURL(models.Model):
    url = models.URLField()
    category = models.ForeignKey(URLCategory, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, default="Unknown")
    last_checked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url


