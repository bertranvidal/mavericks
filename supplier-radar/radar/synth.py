"""Generador de noticias sinteticas por plantillas (sin LLM) para ampliar el dataset de entrenamiento.

La etiqueta se conoce POR CONSTRUCCION, siguiendo los criterios inferidos de las 40 noticias reales:
  urgente = hay parada de suministro y no es corta.
Incluye las trampas: nombres parecidos, lugares sin impacto, noticias positivas.

AVISO: son datos propios. Sirven para ENTRENAR. Nunca se usan para MEDIR: la medida es la validacion real.

  python3 -m radar.synth --n 800 --seed 7      # escribe data/synthetic.csv
"""
import argparse
import random

import pandas as pd

from .config import DATA
from .data import load_suppliers
from .knowledge import CITY_ALIASES
from .matcher import core_tokens

SYN_PATH = DATA / "synthetic.csv"


def pretty(name: str) -> str:
    return " ".join(w.capitalize() if w.islower() else w for w in str(name).split())


class Gen:
    def __init__(self, seed: int):
        self.r = random.Random(seed)
        self.s = load_suppliers()
        self.by_city = {}
        for _, x in self.s.iterrows():
            self.by_city.setdefault(x.City, []).append(x.Supplier_ID)
        # region (alias) -> proveedores en las ciudades de esa region
        self.by_region = {}
        for city, aliases in CITY_ALIASES.items():
            for a in aliases:
                if a in ("rhine",):  # el Rin es un caso de ruta, se trata aparte
                    continue
                self.by_region.setdefault(a, set()).update(self.by_city.get(city, []))
        self.by_region = {k: sorted(v) for k, v in self.by_region.items() if v}
        self.row = {x.Supplier_ID: x for _, x in self.s.iterrows()}
        self.n = 0

    # ------------------------------------------------------------------ utilidades
    def pick(self, xs):
        return self.r.choice(xs)

    def out(self, headline, summary, risk, urgent, ids, event):
        self.n += 1
        return {
            "News_ID": f"SYN{self.n:05d}", "Headline": headline, "Summary": summary,
            "Is_Risk": "Y" if risk else "N", "Urgent": "Y" if urgent else "N",
            "Affected_Supplier_IDs": "; ".join(sorted(ids)), "Event_Type": event,
            "Explanation": "synthetic",
        }

    def sup(self, maker=False):
        ids = [i for i, x in self.row.items() if not maker or x.Category not in ("Logistics", "Services")]
        return self.row[self.pick(ids)]

    # ------------------------------------------------------------------ escenarios
    def supplier_incident(self):
        kind = self.pick(["fire_long", "fire_wh", "recall", "licence", "going", "downgrade", "ceo", "acq", "strike", "audit"])
        x = self.sup(maker=kind in ("fire_long", "fire_wh", "recall"))
        N, C, M = x.Supplier_Name, x.City, x.Material_Supplied
        k = self.r.randint(2, 8)
        i = [x.Supplier_ID]
        if kind == "fire_long":
            return self.out(
                f"Fire at {N} plant in {C} halts production",
                f"A fire broke out at the {C} site of {N} and production has stopped. Inspectors expect the plant to stay closed for at least {k} weeks.",
                True, True, i, "Fire / plant incident")
        if kind == "fire_wh":
            return self.out(
                f"Explosion at {N} warehouse in {C}, no injuries",
                f"An explosion damaged a storage building at {N}. Production buildings were not affected, but finished goods stock was lost.",
                True, False, i, "Fire / plant incident")
        if kind == "recall":
            return self.out(
                f"{N} announces recall of {M.lower()} lots",
                f"{N} is recalling several lots after customers reported quality problems. The company is investigating a possible issue at its {C} plant.",
                True, True, i, "Quality recall")
        if kind == "licence":
            return self.out(
                f"Regulator suspends production licence of {N}",
                f"Authorities in {x.Country} have suspended production at {N} after a compliance review. The review could take up to {k} weeks.",
                True, True, i, "Regulatory action")
        if kind == "going":
            return self.out(
                f"{N} flags going-concern doubt after missed payment",
                f"{N} said it missed a scheduled payment to lenders and its auditor has raised doubts about the company's ability to continue operating. Talks with creditors continue.",
                True, True, i, "Financial distress")
        if kind == "downgrade":
            return self.out(
                f"Rating agency downgrades {N}",
                f"A credit rating agency cut its rating on {N}, citing high debt and weaker margins.",
                True, False, i, "Financial distress")
        if kind == "ceo":
            return self.out(
                f"{N} chief executive steps down",
                f"{N} announced that its chief executive has stepped down with immediate effect. The chief operating officer will act as interim chief executive.",
                True, False, i, "Leadership change")
        if kind == "acq":
            comp = self.pick(["Veltrix Pharma", "Norvane Holdings", "Altis Group", "Medora Capital"])
            return self.out(
                f"{comp} agrees to acquire {N}",
                f"{comp}, a competitor of several large drug makers, has agreed to buy {N}. The deal is expected to close next year.",
                True, False, i, "Acquisition by competitor")
        if kind == "strike":
            return self.out(
                f"Workers at {N} in {C} begin {k % 4 + 2}-day strike",
                f"Staff at the {C} site of {N} have walked out over pay. The company expects some delayed shipments.",
                True, False, i, "Labour strike")
        return self.out(  # audit: positive
            f"{N} completes inspection with no observations",
            f"Inspectors found no observations during the audit of {N}'s {C} facility, the company said.",
            False, False, i, "Positive news")

    def positive(self):
        x = self.sup()
        N, C = x.Supplier_Name, x.City
        h, s = self.pick([
            (f"{N} doubles capacity at {C} site", f"{N} has opened a new production line at its {C} site, doubling output."),
            (f"{N} signs long-term supply deal with European pharma group", f"{N} signed a multi-year contract to supply a large European drug maker."),
            (f"{N} secures new financing to expand {C} capacity", f"A group of banks has agreed new financing for {N} to expand its facilities."),
            (f"{N} receives approval to expand {C} site", f"Local authorities approved the expansion plans of {N} in {C}."),
            (f"{N} wins quality award", f"{N} was recognised for its quality record by an industry body."),
        ])
        return self.out(h, s, False, False, [x.Supplier_ID], "Positive news")

    def location_disaster(self):
        use_region = self.r.random() < 0.45 and self.by_region
        if use_region:
            reg = self.pick(list(self.by_region))
            place, ids = reg.title(), self.by_region[reg]
        else:
            city = self.pick(list(self.by_city))
            place, ids = city, self.by_city[city]
        ev, ev_noun = self.pick([
            ("flooding", "Severe flooding"), ("earthquake", "A strong earthquake"), ("wildfire", "Wildfires"),
            ("typhoon", "A typhoon"), ("storm", "A violent storm"), ("heatwave", "An extreme heatwave"),
        ])
        k = self.r.randint(2, 6)
        v = self.pick(["long", "long", "short", "checks"])
        if v == "long":
            return self.out(
                f"{ev_noun} hits {place}, industrial plants closed",
                f"{ev_noun} struck {place}. Many chemical and pharmaceutical plants have stopped production and roads are closed. Officials say recovery could take {k} weeks.",
                True, True, ids, "Natural disaster")
        if v == "short":
            return self.out(
                f"{ev_noun} near {place} prompts temporary factory closures",
                f"Several factories around {place} closed for 48 hours as a precaution. Operations are expected to resume quickly.",
                True, False, ids, "Natural disaster")
        return self.out(
            f"{ev_noun} reported in {place}",
            f"Factories in {place} halted production for safety checks after the event. Other regions reported only light effects.",
            True, False, ids, "Natural disaster")

    def utility_logistics(self):
        kind = self.pick(["power", "blockade", "portstrike", "truckers"])
        if kind == "power":
            reg = self.pick(list(self.by_region))
            return self.out(
                f"Power rationing imposed on {reg.title()} factories",
                f"Factories in {reg.title()} must cut power use by 20 percent for {self.r.randint(1, 3)} weeks as demand for electricity soars.",
                True, False, self.by_region[reg], "Utility outage")
        ports = [c for c in ("Rotterdam", "Antwerp", "Singapore", "Barcelona", "Valencia", "Kaohsiung", "Ho Chi Minh City", "Sao Paulo") if c in self.by_city]
        city = self.pick(ports if kind == "portstrike" else list(self.by_city))
        ids = self.by_city[city]
        if kind == "blockade":
            return self.out(
                f"Protests block highway near {city} for second day",
                f"Demonstrators have blocked a main road near {city}, delaying deliveries in and out of the area.",
                True, False, ids, "Logistics disruption")
        if kind == "portstrike":
            return self.out(
                f"Strike at {city} terminals enters third day",
                f"A strike by terminal workers around {city} has entered its third day, leaving containers waiting.",
                True, False, ids, "Labour strike")
        return self.out(
            f"Truckers call strike over fuel prices near {city}",
            f"A trade association called a three-day strike, threatening road freight from industrial areas including {city}.",
            True, False, ids, "Labour strike")

    def export_restriction(self):
        by_country = {}
        for _, x in self.s.iterrows():
            by_country.setdefault(x.Country, []).append(x)
        country = self.pick([c for c, v in by_country.items() if len(v) >= 2 and "(" not in c])
        mats = sorted({x.Material_Supplied for x in by_country[country]})
        chosen = self.r.sample(mats, k=min(len(mats), self.r.randint(1, 2)))
        first = [m.split()[0].lower() for m in chosen]
        ids = [x.Supplier_ID for x in by_country[country] if x.Material_Supplied.split()[0].lower() in first]
        names = " and ".join(m.lower() for m in chosen)
        return self.out(
            f"{country} announces temporary export restrictions on {names}",
            f"The government of {country} has introduced export licensing for {names} to protect domestic supply.",
            True, True, ids, "Export restriction")

    def route(self):
        if self.r.random() < 0.5:
            return self.out(
                "Shipping lines reroute around Africa as Red Sea tensions escalate",
                "Major container lines are diverting Asia to Europe services around the Cape of Good Hope, adding about two weeks to journey times.",
                True, False, ["S032"], "Logistics disruption")
        return self.out(
            "Low water on the Rhine restricts barge traffic for chemical shippers",
            "Water levels on the Rhine have fallen after a dry summer, forcing barges to carry reduced loads. Chemical distributors along the river warn of slower deliveries.",
            True, False, ["S009", "S039"], "Logistics disruption")

    def noise(self):
        kind = self.pick(["generic", "place", "lookalike"])
        if kind == "generic":
            h, s = self.pick([
                ("Central bank holds interest rates steady", "The bank left rates unchanged and signalled no change for the rest of the year."),
                ("Global smartphone shipments rise 4 percent", "Makers shipped more devices than a year earlier, led by emerging markets."),
                ("Swiss franc strengthens against the euro", "The currency rose to its highest level in months."),
                ("European Parliament debates reform of pharmaceutical legislation", "Lawmakers began a debate on a long-awaited update of drug rules."),
                ("German business confidence improves for second month", "A closely watched survey showed a further rise in sentiment."),
                ("Oil prices edge lower on demand worries", "Crude fell slightly as traders weighed weaker consumption forecasts."),
                ("Tech giant unveils new cloud region", "The company opened a new data centre region to serve European customers."),
            ])
            return self.out(h, s, False, False, [], "Not relevant")
        if kind == "place":
            city = self.pick(list(self.by_city))
            h, s = self.pick([
                (f"Heavy rain expected in {city} this weekend", f"Forecasters expect showers across {city} over the weekend, with no warnings issued."),
                (f"{city} hosts European logistics summit", f"Industry leaders gather in {city} this week to discuss trends."),
                (f"{city} airport passenger numbers reach record", f"The airport serving {city} handled more travellers than ever before."),
                (f"{city} hosts international AI conference", f"Researchers and companies meet in {city} for a three-day conference."),
                (f"New cultural festival announced in {city}", f"{city} will host a music and film festival next summer."),
            ])
            return self.out(h, s, False, False, [], "Not relevant")
        # nombre parecido: primera palabra distintiva de un proveedor, en otro contexto
        words = {core_tokens(x.Supplier_Name)[0].capitalize() for _, x in self.s.iterrows() if len(core_tokens(x.Supplier_Name)[0]) >= 4}
        w = self.pick(sorted(words))
        h, s = self.pick([
            (f"{w} Capital raises USD 2 billion for new technology fund", f"Private equity firm {w} Capital has closed its latest fund, which will invest in software companies."),
            (f"{w} tops the box office in its opening weekend", f"The new film '{w}' earned more than expected in cinemas."),
            (f"{w} beat Rangers 2-1 in derby", f"{w} won the match with a late goal in front of a full stadium."),
            (f"{w} Energy commissions 500 MW solar farm", f"Utility {w} Energy has connected a large solar plant to the grid."),
            (f"{w} Air reports quarterly results ahead of expectations", f"Airline {w} Air said profit rose on strong summer demand."),
        ])
        return self.out(h, s, False, False, [], "Not relevant")

    def make(self, n: int) -> pd.DataFrame:
        plan = [
            (self.supplier_incident, 0.22), (self.location_disaster, 0.20), (self.utility_logistics, 0.07),
            (self.export_restriction, 0.05), (self.route, 0.03), (self.positive, 0.08), (self.noise, 0.35),
        ]
        fns, ws = zip(*plan)
        rows = [self.r.choices(fns, ws)[0]() for _ in range(n)]
        df = pd.DataFrame(rows).drop_duplicates(subset=["Headline", "Summary"]).reset_index(drop=True)
        df["text"] = df["Headline"] + ". " + df["Summary"]
        return df


def generate(n: int = 1500, seed: int = 7) -> pd.DataFrame:
    return Gen(seed).make(n)


def load_synth() -> pd.DataFrame:
    if not SYN_PATH.exists():
        df = generate()
        df.to_csv(SYN_PATH, index=False)
    return pd.read_csv(SYN_PATH, keep_default_na=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    df = generate(a.n, a.seed)
    df.to_csv(SYN_PATH, index=False)
    print(f"{len(df)} noticias sinteticas -> {SYN_PATH}")
    print(df[["Is_Risk", "Urgent"]].value_counts().to_string())
    print(df["Event_Type"].value_counts().to_string())
