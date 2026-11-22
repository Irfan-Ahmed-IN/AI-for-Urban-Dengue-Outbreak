from django.shortcuts import render

from .labels import CITIES, PAIRS
from .services import TIERS, bundle, forecast, history


def home(request):
    bn = request.GET.get("lang", request.COOKIES.get("dg_lang")) == "bn"
    lang = "bn" if bn else "en"
    response = render(request, "prediction/home.html", {"lang": lang, "bn": bn})
    response.set_cookie("dg_lang", lang, max_age=31536000, samesite="Lax")
    return response


def dashboard(request):
    q = request.GET
    bn = q.get("lang", request.COOKIES.get("dg_lang")) == "bn"
    lang = "bn" if bn else "en"
    t = {key: values[int(bn)] for key, values in PAIRS.items()}
    digits = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

    def local(value):
        return str(value).translate(digits) if bn else str(value)

    ctx = {"t": t, "lang": lang}
    status = 200
    try:
        df = history()
    except (OSError, ValueError, KeyError):
        ctx["error"] = t["data_error"]
        status = 503
    else:
        pairs = list(df.groupby(["city", "ward_id"], sort=True).groups)
        def display(pair):
            city, ward = pair
            return f"{CITIES.get(city, city) if bn else city} · {ward}"
        options = {"|".join(pair): display(pair) for pair in pairs}
        selected = q.get("ward", next(iter(options)))
        # Accept the original dashboard's ward-only query when unambiguous.
        if selected not in options:
            matches = [key for key in options if key.split("|", 1)[1] == selected]
            if len(matches) == 1:
                selected = matches[0]
        try:
            if selected not in options or q.get("horizon", "2") not in ("2", "3", "4"):
                raise ValueError()
            city, ward = selected.split("|", 1)
            rows = df[(df.city == city) & (df.ward_id == ward)]
            dates = rows.date.dt.strftime("%Y-%m-%d").tolist()
            issued = q.get("week") or dates[-1]
            row = rows.iloc[dates.index(issued)]
            horizon = int(q.get("horizon", 2))
            estimate, tier, target = forecast(row, horizon)
        except ValueError:
            status = 400
            ctx["error"] = t["error"]
        else:
            rain = [row[f"rainfall_lag_{n}w"] for n in (4, 3, 2, 1)] + [row.rainfall_mm]
            labels = [f"{local(n)} {t['ago']}" for n in (4, 3, 2)] + [t["weekago"], t["current"]]
            a, b, c = bundle()["risk_cutoffs"]
            ctx.update(
                wards=options.items(), selected=selected, location=options[selected],
                dates=[(d,local(d)) for d in reversed(dates)], issued=issued,
                observation=local(issued), horizon=horizon, horizons=[(n,local(n)) for n in (2,3,4)],
                target=local(target.date()), estimate=local(f"{estimate:.2f}"),
                tier=tier, risk=t[tier], city_count=local(df.city.nunique()), ward_count=local(len(pairs)),
                weather=[(t["rain"],local(row.rainfall_mm),"mm"),(t["temp"],local(row.avg_temp_c),"°C"),
                         (t["humidity"],local(row.relative_humidity_pct),"%")],
                rain_rows=[(label,local(f"{v:.2f}"), round(100*v/(max(rain) or 1))) for label,v in zip(labels,rain)],
                scales=[(k,t[k],local(bounds)) for k,bounds in zip(TIERS,[f"< {a}",f"{a} – < {b}",f"{b} – < {c}",f"≥ {c}"])],
                indicators=[(t[k], local(v)) for k,v in [("cases",row.dengue_cases),("density",f"{row.population_density_sqkm:,}"),
                            ("water",row.water_logging_risk_index),("sanitation",row.sanitation_score)]],
                metrics=[(local(n),local(mae),local(base)) for n,mae,base in [(2,"1.05","1.80"),(3,"1.19","2.11"),(4,"1.38","2.34")]])
    switch = q.copy()
    switch["lang"] = "en" if bn else "bn"
    ctx["switch"] = switch.urlencode()
    response = render(request, "prediction/dashboard.html", ctx, status=status)
    response.set_cookie("dg_lang", lang, max_age=31536000, samesite="Lax")
    return response
