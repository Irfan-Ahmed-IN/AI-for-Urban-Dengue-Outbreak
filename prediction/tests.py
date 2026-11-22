import numpy as np
import pandas as pd
from django.test import TestCase
from django.urls import reverse
from .services import DATA, bundle, forecast, history


class DashboardTests(TestCase):
    def test_every_ward_and_horizon(self):
        raw = pd.read_csv(DATA / "weekly_data.csv", parse_dates=["date"])
        prepared = history()
        for _, rows in raw.groupby(["city", "ward_id"]):
            rows = rows.sort_values("date")
            last = rows.iloc[-1].copy()
            row = prepared[(prepared.city == last.city) & (prepared.ward_id == last.ward_id)].iloc[-1]
            np.testing.assert_allclose([row[f"rainfall_lag_{i}w"] for i in range(1, 5)],
                                       rows.rainfall_mm.iloc[-5:-1][::-1])
            self.assertAlmostEqual(row.cases_four_week_mean, rows.dengue_cases.tail(4).mean())
            for h in (2, 3, 4):
                value, tier, target = forecast(row, h)
                self.assertTrue(np.isfinite(value) and value >= 0)
                self.assertEqual(target, last.date + pd.Timedelta(weeks=h))
                self.assertEqual(tier, ("low","medium","high","critical")[sum(value >= x for x in bundle()["risk_cutoffs"])])

    def test_selections_and_language(self):
        params = {"ward":"CCC_Ward_01","week":"2025-07-07","horizon":"4","lang":"bn"}
        response = self.client.get(reverse("dashboard"), params)
        self.assertContains(response, "২০২৫-০৮-০৪")
        self.assertContains(response, "চট্টগ্রাম")
        self.assertContains(self.client.get(reverse("dashboard")), "ওয়ার্ডের পূর্বাভাস")
        self.assertContains(self.client.get(reverse("dashboard"), {"lang":"en"}), "Ward forecast")

    def test_invalid_selection(self):
        for query in [{"horizon":"5"},{"ward":"missing"},{"week":"2016-01-04"}]:
            self.assertEqual(self.client.get(reverse("dashboard"), query).status_code, 400)


class LandingPageTests(TestCase):
    def test_landing_is_home(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI for Urban")
        self.assertContains(response, "Dengue Outbreak")
        self.assertContains(response, reverse("dashboard"))

    def test_dashboard_has_explicit_route(self):
        self.assertEqual(reverse("dashboard"), "/dashboard/")
        self.assertContains(self.client.get(reverse("dashboard")), "Ward forecast")

    def test_bengali_home(self):
        self.assertContains(self.client.get(reverse("home"), {"lang": "bn"}), "ড্যাশবোর্ড চালু করুন")
