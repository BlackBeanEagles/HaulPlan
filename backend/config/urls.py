from django.contrib import admin
from django.urls import path
from planner.views import plan_trip

urlpatterns = [path("admin/", admin.site.urls), path("api/plan/", plan_trip, name="plan_trip")]
