from django.contrib import admin

from .models import CompletionLog, Person, Task, Template


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("display_name", "tg_user_id")
    search_fields = ("display_name", "tg_user_id")


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "interval_days", "effort", "active", "next_due_at", "last_spawned_at")
    list_filter = ("active",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "state",
        "assignee",
        "effort",
        "source",
        "created_at",
        "next_reminder_at",
        "reminder_level",
    )
    list_filter = ("state", "source")
    search_fields = ("title",)


@admin.register(CompletionLog)
class CompletionLogAdmin(admin.ModelAdmin):
    list_display = ("person", "task", "effort", "completed_at")
    list_filter = ("person",)
