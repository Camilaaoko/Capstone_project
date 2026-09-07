"""Synthetic Healthcare Supply-Chain Intelligence Platform dataset generator.

This script produces a fully synthetic, relational healthcare supply-chain
dataset for a university capstone project. All values are generated from
statistical models with a fixed random seed. The data is NOT real KEMSA data
and must not be presented as such.
"""

import argparse
import math
import os
import sqlite3
from datetime import date, timedelta

import numpy as np
import pandas as pd

RANDOM_SEED = 42
START_DATE = date(2024, 1, 1)
REFERENCE_VISITS = 350.0

COUNTIES = {
    # Coast Region
    "Mombasa": {"factor": 1.15, "center": (-4.0435, 39.6682), "subs": ["Mvita", "Kisauni", "Nyali", "Changamwe", "Jomvu", "Likoni"]},
    "Kwale": {"factor": 0.90, "center": (-4.1744, 39.4521), "subs": ["Matuga", "Msambweni", "Lungalunga", "Kinango"]},
    "Kilifi": {"factor": 0.95, "center": (-3.5107, 39.9093), "subs": ["Kilifi North", "Kilifi South", "Malindi", "Kaloleni", "Ganze", "Magarini", "Rabai"]},
    "Tana River": {"factor": 0.85, "center": (-1.5000, 39.5000), "subs": ["Garsen", "Galole", "Bura"]},
    "Lamu": {"factor": 0.80, "center": (-2.2686, 40.9006), "subs": ["Lamu West", "Lamu East"]},
    "Taita Taveta": {"factor": 0.85, "center": (-3.3167, 38.3500), "subs": ["Voi", "Wundanyi", "Mwatate", "Taveta"]},

    # North Eastern Region
    "Garissa": {"factor": 0.90, "center": (-0.4532, 39.6396), "subs": ["Garissa Township", "Balambala", "Lagdera", "Dadaab", "Fafi", "Ijara"]},
    "Wajir": {"factor": 0.85, "center": (1.7471, 40.0573), "subs": ["Wajir East", "Wajir West", "Wajir North", "Wajir South", "Tarbaj", "Eldas"]},
    "Mandera": {"factor": 0.85, "center": (3.9373, 41.8569), "subs": ["Mandera East", "Mandera West", "Mandera South", "Mandera North", "Banissa", "Lafey"]},

    # Eastern Region
    "Marsabit": {"factor": 0.80, "center": (2.3333, 37.9833), "subs": ["Moyale", "North Horr", "Saku", "Laisamis"]},
    "Isiolo": {"factor": 0.85, "center": (0.3546, 37.5822), "subs": ["Isiolo", "Merti", "Garbatulla"]},
    "Meru": {"factor": 0.90, "center": (0.0471, 37.6462), "subs": ["Imenti North", "Imenti South", "Imenti Central", "Buuri", "Igembe North", "Tigania"]},
    "Tharaka-Nithi": {"factor": 0.85, "center": (-0.2965, 37.7289), "subs": ["Chuka", "Igambang'ombe", "Maara", "Tharaka North", "Tharaka South"]},
    "Embu": {"factor": 0.90, "center": (-0.5312, 37.4555), "subs": ["Manyatta", "Runyenjes", "Mbeere North", "Mbeere South"]},
    "Kitui": {"factor": 0.90, "center": (-1.3667, 38.0167), "subs": ["Kitui Central", "Kitui Rural", "Kitui East", "Kitui South", "Kitui West", "Mwingi Central"]},
    "Machakos": {"factor": 0.95, "center": (-1.5177, 37.2634), "subs": ["Machakos Town", "Mwala", "Yatta", "Kangundo", "Masinga", "Kathiani", "Mavoko"]},
    "Makueni": {"factor": 0.90, "center": (-1.8041, 37.6203), "subs": ["Makueni", "Kaiti", "Kibwezi East", "Kibwezi West", "Kilome", "Mbooni"]},

    # Central Region
    "Nyandarua": {"factor": 0.85, "center": (-0.1804, 36.5230), "subs": ["Ol Kalou", "Kinangop", "Kipipiri", "Ndaragwa", "Ol Joro Orok"]},
    "Nyeri": {"factor": 0.95, "center": (-0.4167, 36.9500), "subs": ["Nyeri Town", "Kieni", "Mathira", "Mukurweini", "Othaya", "Tetu"]},
    "Kirinyaga": {"factor": 0.90, "center": (-0.5000, 37.2833), "subs": ["Kirinyaga Central", "Gichugu", "Mwea", "Ndia"]},
    "Murang'a": {"factor": 0.90, "center": (-0.7167, 37.1500), "subs": ["Kiharu", "Kangema", "Mathioya", "Kigumo", "Kandara", "Gatanga"]},
    "Kiambu": {"factor": 1.10, "center": (-1.1714, 36.8358), "subs": ["Thika", "Ruiru", "Gatundu North", "Githunguri", "Kikuyu", "Limuru", "Juja", "Kabete"]},

    # Rift Valley Region
    "Turkana": {"factor": 0.90, "center": (3.1167, 35.6000), "subs": ["Turkana Central", "Turkana North", "Turkana South", "Turkana West", "Loima"]},
    "West Pokot": {"factor": 0.85, "center": (1.2333, 35.1167), "subs": ["Kapenguria", "Sigor", "Kacheliba", "Pokot South"]},
    "Samburu": {"factor": 0.80, "center": (1.2167, 36.9333), "subs": ["Samburu West", "Samburu East", "Samburu North"]},
    "Trans Nzoia": {"factor": 0.95, "center": (1.0167, 35.0000), "subs": ["Cherangany", "Endebess", "Kiminini", "Kwanza", "Saboti"]},
    "Uasin Gishu": {"factor": 1.05, "center": (0.5143, 35.2698), "subs": ["Soy", "Turbo", "Moiben", "Ainabkoi", "Kesses", "Kapseret"]},
    "Elgeyo-Marakwet": {"factor": 0.85, "center": (0.6833, 35.5167), "subs": ["Keiyo North", "Keiyo South", "Marakwet East", "Marakwet West"]},
    "Nandi": {"factor": 0.90, "center": (0.1833, 35.1000), "subs": ["Aldai", "Chesumei", "Emgwen", "Mosop", "Nandi Hills", "Tinderet"]},
    "Baringo": {"factor": 0.85, "center": (0.4667, 35.9667), "subs": ["Baringo Central", "Baringo North", "Baringo South", "Eldama Ravine", "Mogotio", "Tiaty"]},
    "Laikipia": {"factor": 0.90, "center": (0.3606, 36.7820), "subs": ["Laikipia East", "Laikipia North", "Laikipia West"]},
    "Nakuru": {"factor": 1.05, "center": (-0.3031, 36.0800), "subs": ["Nakuru East", "Nakuru West", "Naivasha", "Gilgil", "Bahati", "Rongai", "Molo", "Njoro"]},
    "Narok": {"factor": 0.90, "center": (-1.0833, 35.8667), "subs": ["Narok North", "Narok South", "Narok East", "Narok West", "Kilgoris"]},
    "Kajiado": {"factor": 0.95, "center": (-1.8500, 36.7833), "subs": ["Kajiado Central", "Kajiado East", "Kajiado North", "Kajiado South", "Kajiado West"]},
    "Kericho": {"factor": 0.90, "center": (-0.3689, 35.2863), "subs": ["Ainamoi", "Belgut", "Bureti", "Kipkelion East", "Kipkelion West", "Soin/Sigowet"]},
    "Bomet": {"factor": 0.90, "center": (-0.7813, 35.3416), "subs": ["Bomet Central", "Bomet East", "Chepalungu", "Konoin", "Sotik"]},

    # Western Region
    "Kakamega": {"factor": 1.00, "center": (0.2833, 34.7500), "subs": ["Lurambi", "Ikolomani", "Shinyalu", "Malava", "Mumias East", "Mumias West", "Butere", "Lugari"]},
    "Vihiga": {"factor": 0.90, "center": (0.0833, 34.7167), "subs": ["Vihiga", "Sabatia", "Hamisi", "Luanda", "Emuhaya"]},
    "Bungoma": {"factor": 0.90, "center": (0.5695, 34.5584), "subs": ["Bungoma Central", "Bungoma East", "Bungoma North", "Bungoma South", "Mt. Elgon", "Webuye"]},
    "Busia": {"factor": 0.90, "center": (0.4608, 34.1115), "subs": ["Budalangi", "Funyula", "Butula", "Matayos", "Nambale", "Teso North", "Teso South"]},

    # Nyanza Region
    "Siaya": {"factor": 0.90, "center": (0.0607, 34.2882), "subs": ["Alego Usonga", "Bondo", "Gem", "Rarieda", "Ugenya", "Ugunja"]},
    "Kisumu": {"factor": 1.15, "center": (-0.0917, 34.7680), "subs": ["Kisumu Central", "Kisumu East", "Kisumu West", "Seme", "Nyando", "Muhoroni", "Nyakach"]},
    "Homa Bay": {"factor": 0.90, "center": (-0.5273, 34.4571), "subs": ["Homa Bay Town", "Kasipul", "Karachuonyo", "Ndhiwa", "Rangwe", "Suba North", "Suba South"]},
    "Migori": {"factor": 0.90, "center": (-1.0634, 34.4731), "subs": ["Suna East", "Suna West", "Uriri", "Awendo", "Rongo", "Nyatike", "Kuria East", "Kuria West"]},
    "Kisii": {"factor": 0.95, "center": (-0.6817, 34.7667), "subs": ["Kitutu Chache", "Nyaribari Chache", "Bonchari", "Bomachoge", "Bobasi", "South Mugirango"]},
    "Nyamira": {"factor": 0.85, "center": (-0.5633, 34.9358), "subs": ["Nyamira Town", "Borabu", "Manga", "Masaba North"]},

    # Nairobi Metro
    "Nairobi": {"factor": 1.25, "center": (-1.2921, 36.8219), "subs": ["Westlands", "Langata", "Embakasi", "Kamukunji", "Dagoretti", "Makadara", "Roysambu", "Kasarani", "Starehe", "Kibra"]},
}

WAREHOUSES = [
    ("WH001", "KEMSA National Central Warehouse", "Central", "Nairobi", (-1.2921, 36.8219), 2000000),
    ("WH002", "KEMSA Mombasa Regional Warehouse", "Coast", "Mombasa", (-4.0435, 39.6682), 800000),
    ("WH003", "KEMSA Kisumu Regional Warehouse", "Nyanza/Western", "Kisumu", (-0.0917, 34.7680), 700000),
    ("WH004", "KEMSA Nakuru Regional Warehouse", "Rift Valley", "Nakuru", (-0.3031, 36.0800), 900000),
    ("WH005", "KEMSA Embu Regional Warehouse", "Eastern", "Embu", (-0.5312, 37.4555), 600000),
    ("WH006", "KEMSA Garissa Regional Warehouse", "North Eastern", "Garissa", (-0.4532, 39.6396), 400000),
]

SUPPLIERS = [
    ("SUP001", "Global Pharma East Africa Ltd", "Multinational manufacturer", 25, 0.92, 0.93),
    ("SUP002", "Naivasha Generics Manufacturing", "Local generic manufacturer", 18, 0.88, 0.86),
    ("SUP003", "Coast Medical Supplies Ltd", "Regional distributor", 12, 0.84, 0.80),
    ("SUP004", "East Africa IV Solutions", "IV fluids manufacturer", 15, 0.90, 0.88),
    ("SUP005", "Vaccine Logistics Partners Ltd", "Cold-chain logistics", 10, 0.95, 0.96),
    ("SUP006", "Rift Valley Pharma Distributors", "Distributor", 14, 0.78, 0.72),
    ("SUP007", "Lake Basin Medical Services", "Distributor", 16, 0.82, 0.79),
    ("SUP008", "Emergency Care Supplies Ltd", "Emergency medicines supplier", 8, 0.94, 0.95),
    ("SUP009", "Northern Frontier Medical Supplies", "Regional distributor", 20, 0.70, 0.65),
    ("SUP010", "Nairobi Medical & Surgical", "Distributor", 10, 0.89, 0.85),
    ("SUP011", "Global Vaccines Initiative", "Vaccine supplier", 22, 0.93, 0.94),
    ("SUP012", "East Africa Chemist Wholesalers", "Wholesaler", 13, 0.86, 0.83),
]

CATEGORY_SUPPLIERS = {
    "Antibiotics": ["SUP001", "SUP002", "SUP006", "SUP010"],
    "Analgesics": ["SUP001", "SUP007", "SUP010"],
    "Antimalarials": ["SUP001", "SUP007", "SUP010"],
    "IV Fluids": ["SUP004", "SUP006", "SUP010"],
    "Maternal Health": ["SUP001", "SUP005", "SUP008"],
    "Pediatric Medicines": ["SUP001", "SUP007", "SUP010"],
    "Diabetes Medicines": ["SUP001", "SUP002", "SUP010"],
    "Hypertension Medicines": ["SUP001", "SUP007", "SUP010"],
    "Vaccination": ["SUP005", "SUP011"],
    "Emergency Medicines": ["SUP008", "SUP010"],
}

# commodity: id, name, category, dosage_form, uom, pack_size, unit_cost,
# lead_time_days, safety_stock_days, shelf_life_days, criticality_level,
# popularity (units / 1000 visits / day), season_type, noise_sigma
COMMODITY_SPECS = [
    ("COM001", "Amoxicillin 250mg capsules", "Antibiotics", "Capsules", "capsule", 100, 3.2, 14, 10, 1095, "HIGH", 12.0, "stable", 0.20),
    ("COM002", "Amoxicillin/Clavulanic Acid 625mg", "Antibiotics", "Tablets", "tablet", 100, 28.0, 18, 10, 730, "HIGH", 2.0, "stable", 0.25),
    ("COM003", "Ciprofloxacin 500mg", "Antibiotics", "Tablets", "tablet", 100, 12.0, 14, 7, 1095, "MEDIUM", 3.0, "stable", 0.20),
    ("COM004", "Azithromycin 250mg", "Antibiotics", "Tablets", "tablet", 30, 25.0, 20, 7, 1095, "MEDIUM", 1.5, "stable", 0.25),
    ("COM005", "Ceftriaxone 1g injection", "Antibiotics", "Injection", "vial", 10, 45.0, 12, 10, 730, "HIGH", 2.0, "stable", 0.25),
    ("COM006", "Metronidazole 400mg", "Antibiotics", "Tablets", "tablet", 100, 4.0, 12, 7, 1095, "MEDIUM", 8.0, "stable", 0.20),
    ("COM007", "Doxycycline 100mg", "Antibiotics", "Capsules", "capsule", 100, 6.0, 14, 7, 1095, "MEDIUM", 2.5, "wet", 0.25),
    ("COM008", "Co-trimoxazole 480mg", "Antibiotics", "Tablets", "tablet", 100, 5.0, 12, 7, 1095, "MEDIUM", 6.0, "stable", 0.20),
    ("COM009", "Paracetamol 500mg", "Analgesics", "Tablets", "tablet", 100, 1.5, 10, 7, 1095, "MEDIUM", 25.0, "winter", 0.18),
    ("COM010", "Paracetamol Syrup 120mg/5ml", "Analgesics", "Syrup", "bottle", 10, 40.0, 12, 10, 730, "HIGH", 5.0, "winter", 0.22),
    ("COM011", "Ibuprofen 400mg", "Analgesics", "Tablets", "tablet", 100, 5.0, 12, 7, 1095, "LOW", 8.0, "stable", 0.20),
    ("COM012", "Diclofenac 75mg injection", "Analgesics", "Injection", "vial", 10, 20.0, 12, 7, 730, "LOW", 1.2, "stable", 0.30),
    ("COM013", "Tramadol 50mg", "Analgesics", "Tablets", "tablet", 100, 18.0, 15, 7, 1095, "MEDIUM", 1.5, "stable", 0.25),
    ("COM014", "Artemether/Lumefantrine 20/120mg", "Antimalarials", "Tablets", "tablet", 24, 35.0, 15, 10, 730, "HIGH", 6.0, "wet", 0.25),
    ("COM015", "Quinine Sulphate 300mg", "Antimalarials", "Tablets", "tablet", 100, 22.0, 18, 7, 1095, "MEDIUM", 1.5, "wet", 0.25),
    ("COM016", "Sulfadoxine/Pyrimethamine 500/25mg", "Antimalarials", "Tablets", "tablet", 100, 8.0, 15, 10, 1095, "HIGH", 3.0, "wet", 0.25),
    ("COM017", "Primaquine 7.5mg", "Antimalarials", "Tablets", "tablet", 100, 9.0, 18, 4, 1095, "LOW", 0.8, "wet", 0.30),
    ("COM018", "Normal Saline 0.9% 1L", "IV Fluids", "IV solution", "bag", 10, 85.0, 12, 10, 730, "HIGH", 5.0, "stable", 0.22),
    ("COM019", "Ringer's Lactate 1L", "IV Fluids", "IV solution", "bag", 10, 90.0, 12, 10, 730, "HIGH", 4.0, "stable", 0.22),
    ("COM020", "Dextrose 5% 500ml", "IV Fluids", "IV solution", "bag", 10, 80.0, 12, 7, 730, "MEDIUM", 3.0, "stable", 0.22),
    ("COM021", "Dextrose 10% 500ml", "IV Fluids", "IV solution", "bag", 10, 85.0, 14, 7, 730, "MEDIUM", 0.8, "stable", 0.30),
    ("COM022", "Oxytocin 10IU/ml injection", "Maternal Health", "Injection", "vial", 10, 30.0, 12, 10, 365, "HIGH", 1.5, "stable", 0.25),
    ("COM023", "Magnesium Sulfate 50% 10ml", "Maternal Health", "Injection", "vial", 10, 45.0, 14, 10, 730, "HIGH", 1.0, "stable", 0.30),
    ("COM024", "Misoprostol 200mcg", "Maternal Health", "Tablets", "tablet", 28, 15.0, 18, 10, 730, "HIGH", 0.8, "stable", 0.30),
    ("COM025", "Iron + Folic Acid 60/400mcg", "Maternal Health", "Tablets", "tablet", 100, 3.0, 12, 7, 1095, "MEDIUM", 10.0, "stable", 0.20),
    ("COM026", "Tetanus Toxoid Vaccine", "Maternal Health", "Injection", "vial", 10, 60.0, 15, 10, 540, "HIGH", 0.6, "campaign", 0.30),
    ("COM027", "Oral Rehydration Salts sachet", "Pediatric Medicines", "Sachet", "sachet", 20, 8.0, 10, 10, 730, "HIGH", 8.0, "spike", 0.30),
    ("COM028", "Zinc Sulphate 20mg", "Pediatric Medicines", "Tablets", "tablet", 100, 6.0, 12, 7, 1095, "HIGH", 3.0, "stable", 0.25),
    ("COM029", "Vitamin A 200,000IU", "Pediatric Medicines", "Capsules", "capsule", 100, 4.0, 15, 10, 730, "HIGH", 2.5, "campaign", 0.30),
    ("COM030", "Co-trimoxazole Syrup 200/40mg/5ml", "Pediatric Medicines", "Syrup", "bottle", 10, 35.0, 12, 7, 730, "MEDIUM", 3.0, "stable", 0.22),
    ("COM031", "Metformin 500mg", "Diabetes Medicines", "Tablets", "tablet", 100, 4.0, 12, 7, 1095, "MEDIUM", 4.0, "stable", 0.20),
    ("COM032", "Glibenclamide 5mg", "Diabetes Medicines", "Tablets", "tablet", 100, 5.0, 12, 7, 1095, "MEDIUM", 1.5, "stable", 0.20),
    ("COM033", "Insulin 100IU/ml vial", "Diabetes Medicines", "Injection", "vial", 10, 300.0, 20, 10, 365, "HIGH", 1.2, "stable", 0.25),
    ("COM034", "Blood Glucose Test Strips", "Diabetes Medicines", "Consumable", "strip", 50, 8.0, 14, 7, 730, "MEDIUM", 2.0, "stable", 0.20),
    ("COM035", "Amlodipine 5mg", "Hypertension Medicines", "Tablets", "tablet", 100, 6.0, 12, 7, 1095, "MEDIUM", 5.0, "stable", 0.18),
    ("COM036", "Nifedipine 30mg", "Hypertension Medicines", "Tablets", "tablet", 100, 7.0, 12, 7, 1095, "MEDIUM", 2.0, "stable", 0.20),
    ("COM037", "Hydrochlorothiazide 25mg", "Hypertension Medicines", "Tablets", "tablet", 100, 4.0, 12, 7, 1095, "MEDIUM", 2.5, "stable", 0.20),
    ("COM038", "Measles-Rubella Vaccine", "Vaccination", "Injection", "vial", 10, 120.0, 15, 10, 540, "HIGH", 0.8, "campaign", 0.30),
    ("COM039", "Oral Polio Vaccine", "Vaccination", "Oral drops", "vial", 10, 90.0, 15, 10, 365, "HIGH", 0.8, "campaign", 0.30),
    ("COM040", "Auto-Disable Syringe 0.5ml", "Vaccination", "Medical device", "syringe", 100, 5.0, 10, 7, 1095, "HIGH", 3.0, "campaign", 0.25),
    ("COM041", "Adrenaline 1mg/ml injection", "Emergency Medicines", "Injection", "ampoule", 10, 25.0, 8, 14, 730, "CRITICAL", 0.5, "stable", 0.35),
    ("COM042", "Hydrocortisone 100mg injection", "Emergency Medicines", "Injection", "vial", 10, 30.0, 10, 14, 730, "CRITICAL", 0.8, "stable", 0.30),
    ("COM043", "Diazepam 10mg injection", "Emergency Medicines", "Injection", "ampoule", 10, 20.0, 10, 14, 1095, "CRITICAL", 0.6, "stable", 0.30),
    ("COM044", "Furosemide 40mg", "Emergency Medicines", "Tablets", "tablet", 100, 6.0, 12, 14, 1095, "HIGH", 2.0, "stable", 0.22),
    ("COM045", "Mebendazole 500mg", "Pediatric Medicines", "Tablets", "tablet", 100, 4.0, 12, 7, 1095, "MEDIUM", 3.0, "campaign", 0.30),
]

DEMAND_EVENTS = [
    ("EVA001", "SEASONAL_INCREASE", date(2024, 4, 15), date(2024, 6, 30),
     ["Kisumu", "Mombasa", "Kilifi", "Bungoma"], ["Antimalarials", "IV Fluids", "Analgesics"], 1.6, "MEDIUM", "Malaria_Season_2024"),
    ("EVA002", "OUTBREAK_SIMULATION", date(2024, 7, 1), date(2024, 9, 30),
     ["Nairobi", "Mombasa", "Kisumu"], ["Pediatric Medicines", "Antibiotics", "IV Fluids"], 2.1, "HIGH", "Cholera_Outbreak_2024"),
    ("EVA003", "PUBLIC_HEALTH_CAMPAIGN", date(2024, 10, 14), date(2024, 10, 25),
     list(COUNTIES.keys()), ["Pediatric Medicines"], 1.8, "MEDIUM", "Deworming_Campaign_2024"),
    ("EVA004", "SUPPLY_DISRUPTION", date(2024, 8, 15), date(2024, 9, 14),
     list(COUNTIES.keys()), list(CATEGORY_SUPPLIERS.keys()), 1.0, "HIGH", "Transport_Strike_2024"),
    ("EVA005", "SEASONAL_INCREASE", date(2024, 11, 1), date(2024, 12, 31),
     list(COUNTIES.keys()), ["Analgesics", "Antibiotics"], 1.3, "LOW", "Cold_Season_2024"),
    ("EVA006", "PUBLIC_HEALTH_CAMPAIGN", date(2025, 1, 20), date(2025, 2, 14),
     ["Nairobi", "Mombasa", "Kiambu"], ["Vaccination"], 1.7, "MEDIUM", "Measles_Rubella_Campaign_2025"),
    ("EVA007", "SEASONAL_INCREASE", date(2025, 4, 15), date(2025, 6, 30),
     ["Kisumu", "Mombasa", "Kilifi", "Bungoma"], ["Antimalarials", "IV Fluids", "Analgesics"], 1.7, "MEDIUM", "Malaria_Season_2025"),
    ("EVA008", "DEMAND_SPIKE", date(2025, 7, 7), date(2025, 7, 20),
     ["Kisumu", "Nairobi", "Machakos"], ["Pediatric Medicines", "Antibiotics", "IV Fluids"], 2.0, "HIGH", "Flood_2025_Demand_Spike"),
    ("EVA009", "SEASONAL_INCREASE", date(2025, 11, 1), date(2025, 12, 31),
     list(COUNTIES.keys()), ["Analgesics", "Antibiotics"], 1.3, "LOW", "Cold_Season_2025"),
    ("EVA010", "NORMAL", date(2024, 1, 1), date(2025, 12, 31),
     list(COUNTIES.keys()), list(CATEGORY_SUPPLIERS.keys()), 1.0, "NONE", "Normal_Baseline"),
]

# commodity, county, facility type, role  (role in SURPLUS / STRESS / NORMAL)
DESIGNED_SCENARIOS = [
    ("COM014", "Kisumu", "County Referral Hospital", "SURPLUS"),
    ("COM014", "Kisumu", "Health Centre", "STRESS"),
    ("COM014", "Kilifi", "County Referral Hospital", "SURPLUS"),
    ("COM014", "Kilifi", "Dispensary", "STRESS"),
    ("COM027", "Mombasa", "County Referral Hospital", "SURPLUS"),
    ("COM027", "Mombasa", "Dispensary", "STRESS"),
    ("COM027", "Nairobi", "County Referral Hospital", "SURPLUS"),
    ("COM027", "Nairobi", "Sub-County Hospital", "STRESS"),
    ("COM009", "Nakuru", "County Referral Hospital", "SURPLUS"),
    ("COM009", "Nakuru", "Health Centre", "STRESS"),
    ("COM009", "Nairobi", "County Referral Hospital", "SURPLUS"),
    ("COM009", "Kiambu", "Sub-County Hospital", "STRESS"),
    ("COM001", "Nairobi", "County Referral Hospital", "SURPLUS"),
    ("COM001", "Nairobi", "Sub-County Hospital", "STRESS"),
    ("COM001", "Nairobi", "Health Centre", "NORMAL"),
    ("COM001", "Uasin Gishu", "County Referral Hospital", "SURPLUS"),
    ("COM001", "Bungoma", "Sub-County Hospital", "STRESS"),
    ("COM045", "Meru", "County Referral Hospital", "SURPLUS"),
    ("COM045", "Meru", "Dispensary", "STRESS"),
    ("COM045", "Bungoma", "County Referral Hospital", "SURPLUS"),
    ("COM045", "Bungoma", "Health Centre", "STRESS"),
    ("COM031", "Machakos", "County Referral Hospital", "SURPLUS"),
    ("COM031", "Machakos", "Sub-County Hospital", "STRESS"),
    ("COM005", "Mombasa", "County Referral Hospital", "SURPLUS"),
    ("COM005", "Mombasa", "Health Centre", "STRESS"),
]

FACILITY_LEVELS = {
    "National Referral Hospital": ("Level 6", 700, 1400, 1800, 3200),
    "County Referral Hospital": ("Level 5", 200, 500, 700, 1400),
    "Sub-County Hospital": ("Level 4", 80, 220, 250, 550),
    "Health Centre": ("Level 3", 20, 60, 90, 200),
    "Dispensary": ("Level 2", 4, 20, 30, 80),
}

VILLAGE_NAMES = [
    "Kwa Mwangi", "Mji Mwema", "Baraka", "Chembe", "Shamba", "Kitui", "Nembu",
    "Soin", "Tulwet", "Karuri", "Manyatta", "Kiptere", "Mkwajuni", "Ongata",
    "Githima", "Bongom", "Rongai Centre", "Mariakani", "Ithanga", "Sigor",
]


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def gaussian_wave(day, peak, width):
    return math.exp(-((day - peak) ** 2) / (2 * width ** 2))


NUMERIC_COLUMNS = {
    "INVENTORY": {"opening_stock", "quantity_received", "quantity_issued",
                  "quantity_adjusted", "closing_stock"},
    "CONSUMPTION": {"quantity_consumed", "patient_demand_index", "seasonality_factor"},
}


class ChunkWriter:
    def __init__(self, output_dir, table, columns, conn=None, chunk=200000):
        self.csv_path = os.path.join(output_dir, table + ".csv")
        if os.path.exists(self.csv_path):
            os.remove(self.csv_path)
        self.columns = list(columns)
        self.conn = conn
        self.chunk = chunk
        self.buf = []
        self.wrote_header = False

    def add_row(self, row):
        self.buf.append(row)
        if len(self.buf) >= self.chunk:
            self.flush()

    def add_rows(self, rows):
        for r in rows:
            self.buf.append(r)
        if len(self.buf) >= self.chunk:
            self.flush()

    def flush(self):
        if not self.buf:
            return
        frame = pd.DataFrame(self.buf, columns=self.columns)
        frame.to_csv(self.csv_path, mode="a", header=not self.wrote_header, index=False)
        self.wrote_header = True
        if self.conn is not None:
            table = self.table_name()
            numeric = NUMERIC_COLUMNS.get(table, set())
            cols = ", ".join(f'"{c}" REAL' if c in numeric else f'"{c}" TEXT' for c in self.columns)
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} ({cols})")
            placeholders = ",".join(["?"] * len(self.columns))
            sql = f"INSERT INTO {table} VALUES ({placeholders})"
            self.conn.execute("BEGIN")
            self.conn.executemany(sql, self.buf)
            self.conn.commit()
        self.buf = []

    def table_name(self):
        return self.csv_path.split(os.sep)[-1][:-4]

    def close(self):
        self.flush()


class SupplyChainGenerator:
    def __init__(self, n_facilities, n_commodities, months, seed=RANDOM_SEED):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.n_facilities = n_facilities
        self.n_commodities = n_commodities
        self.months = months
        self.month_index_base = START_DATE.year * 12 + START_DATE.month
        self.dates, self.month_ends = self._build_dates()
        self.n_days = len(self.dates)
        self.disruption_days = self._build_disruption_days()

        self.facilities = []
        self.facilities_by_id = {}
        self.warehouses = {w[0]: w for w in WAREHOUSES}
        self.warehouse_list = WAREHOUSES
        self.suppliers = {s[0]: s for s in SUPPLIERS}
        self.commodities = []
        self.commodities_by_id = {}
        self.demand_events = []
        self.pairs = []
        self.modes = {}
        self.profiles = {}

        self.orders = []
        self.shipments = []
        self.batches = []
        self.redis = []
        self.dq_issues = []
        self.scenario_labels = []

        self.stockout_days = 0
        self.stockout_facility_commodity = set()
        self.expired_units = 0.0
        self.emergency_orders = 0

    def _build_dates(self):
        dates = []
        d = START_DATE
        m = 0
        year, month = d.year, d.month
        while m < self.months:
            if month == 12:
                nd = (date(year + 1, 1, 1) - date(year, month, 1)).days
                next_year, next_month = year + 1, 1
            else:
                nd = (date(year, month + 1, 1) - date(year, month, 1)).days
                next_year, next_month = year, month + 1
            for _ in range(nd):
                dates.append(d)
                d += timedelta(days=1)
            m += 1
            year, month = next_year, next_month
        month_ends = []
        idx = self.month_index_base
        counts = {}
        for dt in dates:
            counts[dt.year * 12 + dt.month] = counts.get(dt.year * 12 + dt.month, 0) + 1
        run = 0
        for i, dt in enumerate(dates):
            run += 1
            key = dt.year * 12 + dt.month
            if run == counts[key]:
                month_ends.append(i)
                run = 0
        return dates, month_ends

    def _build_disruption_days(self):
        start = date(2024, 8, 15)
        end = date(2024, 9, 14)
        out = set()
        d = start
        while d <= end:
            out.add(d)
            d += timedelta(days=1)
        return out

    def generate_facilities(self):
        rng = self.rng
        fid = 0
        ordered = [
            ("National Referral Hospital", "Nairobi"),
        ]
        # 1. Level 5: 1 County Referral Hospital per county (47 counties)
        for c in COUNTIES:
            ordered.append(("County Referral Hospital", c))
        # 2. Level 4: Sub-County Hospitals (up to 3 per county)
        for _ in range(3):
            for c in COUNTIES:
                ordered.append(("Sub-County Hospital", c))
        # 3. Level 3: Health Centres (up to 4 per county)
        for _ in range(4):
            for c in COUNTIES:
                ordered.append(("Health Centre", c))
        # 4. Level 2: Dispensaries (up to 4 per county)
        for _ in range(4):
            for c in COUNTIES:
                ordered.append(("Dispensary", c))

        self.scenario_facility_refs = {}
        for ftype, county in ordered:
            fid += 1
            if fid > self.n_facilities:
                break
            ftype_short = ftype.replace("Hospital", "").strip()
            info = COUNTIES[county]
            subs = info["subs"]
            idx = sum(1 for _f in self.facilities if _f["county"] == county)
            sub = subs[idx % len(subs)]
            if ftype == "National Referral Hospital":
                name = f"{county} National Referral Hospital"
            elif ftype == "County Referral Hospital":
                name = f"{county} County Referral Hospital"
            elif ftype == "Sub-County Hospital":
                name = f"{sub} Sub-County Hospital"
            elif ftype == "Health Centre":
                name = f"{sub} Health Centre"
            else:
                village = VILLAGE_NAMES[(idx * 7 + len(county)) % len(VILLAGE_NAMES)]
                name = f"{village} Dispensary"
            level, b_min, b_max, v_min, v_max = FACILITY_LEVELS[ftype]
            lat = info["center"][0] + rng.uniform(-0.12, 0.12)
            lon = info["center"][1] + rng.uniform(-0.12, 0.12)
            beds = int(rng.integers(b_min, b_max + 1))
            visits = float(rng.integers(v_min, v_max + 1))
            facility = {
                "facility_id": f"FAC{fid:04d}",
                "facility_name": name,
                "facility_type": ftype,
                "county": county,
                "sub_county": sub,
                "latitude": round(lat, 5),
                "longitude": round(lon, 5),
                "facility_level": level,
                "bed_capacity": beds,
                "average_daily_patient_visits": round(visits, 1),
                "facility_status": "ACTIVE",
                "county_factor": info["factor"],
                "primary_warehouse": self._nearest_warehouse(lat, lon),
            }
            self.facilities.append(facility)
            self.facilities_by_id[facility["facility_id"]] = facility
            self.scenario_facility_refs.setdefault((county, ftype), []).append(facility["facility_id"])

    def _nearest_warehouse(self, lat, lon):
        best, best_d = None, 1e18
        for w in WAREHOUSES:
            d = haversine_km(lat, lon, w[4][0], w[4][1])
            if d < best_d:
                best, best_d = w[0], d
        return best

    def generate_commodities(self):
        for spec in COMMODITY_SPECS[: self.n_commodities]:
            cid, name, cat, form, uom, pack, cost, lead, safety, shelf, crit, pop, season, sigma = spec
            ref_daily = pop * REFERENCE_VISITS / 1000.0
            min_stock = max(pack, int(math.ceil(ref_daily * 14 / pack) * pack))
            max_stock = max(pack, int(math.ceil(ref_daily * 56 / pack) * pack))
            commodity = {
                "commodity_id": cid,
                "commodity_name": name,
                "category": cat,
                "dosage_form": form,
                "unit_of_measure": uom,
                "pack_size": pack,
                "unit_cost": cost,
                "lead_time_days": lead,
                "minimum_stock_level": min_stock,
                "maximum_stock_level": max_stock,
                "safety_stock_days": safety,
                "shelf_life_days": shelf,
                "criticality_level": crit,
                "popularity": pop,
                "season_type": season,
                "noise_sigma": sigma,
                "ref_daily": ref_daily,
            }
            self.commodities.append(commodity)
            self.commodities_by_id[cid] = commodity

    def generate_events(self):
        for ev in DEMAND_EVENTS:
            self.demand_events.append({
                "event_id": ev[0],
                "event_type": ev[1],
                "start_date": ev[2].isoformat(),
                "end_date": ev[3].isoformat(),
                "affected_counties": ";".join(ev[4]),
                "affected_commodity_categories": ";".join(ev[5]),
                "demand_multiplier": ev[6],
                "severity": ev[7],
                "event_name": ev[8],
            })

    def _seasonality_array(self, commodity):
        n = self.n_days
        out = np.ones(n, dtype=np.float64)
        stype = commodity["season_type"]
        for i, dt in enumerate(self.dates):
            doy = dt.timetuple().tm_yday
            if stype == "wet":
                out[i] = 1.0 + 0.25 * gaussian_wave(doy, 135, 25) + 0.25 * gaussian_wave(doy, 305, 25)
            elif stype == "winter":
                out[i] = 1.0 + 0.20 * gaussian_wave(doy, 215, 30)
            elif stype == "campaign":
                out[i] = 1.0 + 0.10 * math.sin(2 * math.pi * i / 40.0)
            else:
                out[i] = 1.0
        return out

    def _event_arrays(self):
        n = self.n_days
        arrays = {}
        for county in COUNTIES:
            for cat in CATEGORY_SUPPLIERS:
                mult = np.ones(n, dtype=np.float64)
                names = ["NONE"] * n
                arrays[(county, cat)] = (mult, names)
        for ev in self.demand_events:
            ev_id = ev["event_id"]
            event_name = ev["event_name"]
            m = ev["demand_multiplier"]
            if ev_id == "EVA004" or m == 1.0:
                continue
            for county in ev["affected_counties"].split(";"):
                for cat in ev["affected_commodity_categories"].split(";"):
                    if (county, cat) not in arrays:
                        continue
                    mult, names = arrays[(county, cat)]
                    start = date.fromisoformat(ev["start_date"])
                    end = date.fromisoformat(ev["end_date"])
                    for i, dt in enumerate(self.dates):
                        if start <= dt <= end:
                            mult[i] *= m
                            names[i] = event_name
        return arrays

    def assign_modes(self):
        for f in self.facilities:
            for c in self.commodities:
                self.pairs.append((f["facility_id"], c["commodity_id"]))
        resolved = []
        for cid, county, ftype, role in DESIGNED_SCENARIOS:
            fac_ids = self.scenario_facility_refs.get((county, ftype), [])
            if fac_ids:
                resolved.append((fac_ids[0], cid, role))
        for fid, cid, role in resolved:
            self.modes[(fid, cid)] = role
            if role == "SURPLUS":
                self.scenario_labels.append({
                    "scenario_name": "S2_SURPLUS",
                    "commodity_id": cid,
                    "facility_id": fid,
                    "role": "surplus_source",
                    "description": "Designed surplus (over-ordering) facility for scenario 2 / 7.",
                })
            elif role == "STRESS":
                self.scenario_labels.append({
                    "scenario_name": "S1_STOCKOUT_RISK",
                    "commodity_id": cid,
                    "facility_id": fid,
                    "role": "shortage_destination",
                    "description": "Designed stockout-risk (rising demand + delayed supply) facility for scenario 1 / 7.",
                })
            else:
                self.scenario_labels.append({
                    "scenario_name": "S7_NORMAL",
                    "commodity_id": cid,
                    "facility_id": fid,
                    "role": "normal_peer",
                    "description": "Normal-stock peer facility for scenario 7 comparison.",
                })
        for (fid, cid) in self.pairs:
            if (fid, cid) in self.modes:
                continue
            r = self.rng.random()
            shelf = self.commodities_by_id[cid]["shelf_life_days"]
            if r < 0.06:
                self.modes[(fid, cid)] = "SURPLUS"
            elif r < 0.12:
                self.modes[(fid, cid)] = "STRESS"
            elif r < 0.20 and shelf <= 730:
                self.modes[(fid, cid)] = "EXPIRY"
            else:
                self.modes[(fid, cid)] = "NORMAL"
        for cid, county, ftype, role in DESIGNED_SCENARIOS:
            fac_ids = self.scenario_facility_refs.get((county, ftype), [])
            if fac_ids and (fac_ids[0], cid) in self.modes and self.modes[(fac_ids[0], cid)] == "SURPLUS":
                self.scenario_labels.append({
                    "scenario_name": "S3_REDISTRIBUTION",
                    "commodity_id": cid,
                    "facility_id": fac_ids[0],
                    "role": "source",
                    "description": "Designed redistribution chain source (surplus -> shortage).",
                })
            if fac_ids and (fac_ids[0], cid) in self.modes and self.modes[(fac_ids[0], cid)] == "STRESS":
                self.scenario_labels.append({
                    "scenario_name": "S3_REDISTRIBUTION",
                    "commodity_id": cid,
                    "facility_id": fac_ids[0],
                    "role": "destination",
                    "description": "Designed redistribution chain destination (surplus -> shortage).",
                })

    def simulate(self, output_dir, conn):
        inv_w = ChunkWriter(output_dir, "INVENTORY",
                            ["date", "facility_id", "commodity_id", "opening_stock",
                             "quantity_received", "quantity_issued", "quantity_adjusted",
                             "closing_stock", "stock_status"], conn)
        con_w = ChunkWriter(output_dir, "CONSUMPTION",
                            ["date", "facility_id", "commodity_id", "quantity_consumed",
                             "patient_demand_index", "seasonality_factor", "demand_event",
                             "data_quality_flag"], conn)
        rng = self.rng
        dates = self.dates
        n = self.n_days
        month_end_dates = [dates[i] for i in self.month_ends]
        event_arrays = self._event_arrays()
        season_cache = {}
        for c in self.commodities:
            season_cache[c["commodity_id"]] = self._seasonality_array(c)
        dup_consumption = []

        order_seq = 0
        shipment_seq = 0
        batch_seq = 0

        for (fid, cid) in self.pairs:
            mode = self.modes[(fid, cid)]
            fac = self.facilities_by_id[fid]
            com = self.commodities_by_id[cid]
            visits = fac["average_daily_patient_visits"]
            base = com["popularity"] * visits / 1000.0
            cf = fac["county_factor"]
            season = season_cache[cid]
            ev_mult, ev_names = event_arrays[(fac["county"], com["category"])]
            if mode == "STRESS":
                trend = 1.0 + 0.45 * np.arange(n) / n
                order_factor = 0.70
                sigma = com["noise_sigma"] + 0.05
            elif mode == "SURPLUS":
                trend = 1.0 - 0.02 * np.arange(n) / n
                order_factor = 1.50
                sigma = com["noise_sigma"]
            elif mode == "EXPIRY":
                trend = np.full(n, 0.55)
                order_factor = 0.90
                sigma = com["noise_sigma"]
            else:
                trend = 1.0 + 0.05 * np.arange(n) / n
                order_factor = 1.0
                sigma = com["noise_sigma"]
            noise = rng.lognormal(0.0, sigma, n)
            sems = season * ev_mult
            demand = base * cf * sems * trend * noise
            expected = base * cf * float(np.mean(season * ev_mult))
            pack = com["pack_size"]
            lead = com["lead_time_days"]
            safety_days = com["safety_stock_days"]
            ref_ratio = visits / REFERENCE_VISITS
            min_scaled = max(1.0, com["minimum_stock_level"] * ref_ratio)
            max_scaled = max(2.0, com["maximum_stock_level"] * ref_ratio)
            if max_scaled < min_scaled * 1.5:
                max_scaled = min_scaled * 1.5
            safety_level = safety_days * expected
            reorder_point = max(1.0, (lead + safety_days) * expected)
            stock = float(rng.uniform(min_scaled * 0.8, max_scaled * 0.75))
            if mode == "EXPIRY":
                stock = max_scaled * rng.uniform(0.85, 0.95)

            batches = []
            ended_batches = []
            initial_expiry = dates[0] + timedelta(days=int(rng.uniform(0.3, 0.6) * com["shelf_life_days"]))
            batches.append({
                "batch_id": f"BAT{batch_seq + 1:07d}", "commodity_id": cid, "facility_id": fid,
                "received_date": dates[0],
                "manufacturing_date": dates[0] - timedelta(days=int(rng.uniform(0.2, 0.5) * com["shelf_life_days"])),
                "expiry_date": initial_expiry, "initial_quantity": stock, "remaining_quantity": stock,
                "status": "ACTIVE", "sequence": 0,
            })
            batch_seq += 1

            pending = None
            adj_mask = rng.random(n) < 0.004
            adj_amt = rng.integers(1, 5, n).astype(float)
            exp_short = mode == "EXPIRY" or rng.random() < 0.10

            month_close_end = [0.0] * self.months
            month_max_close = [0.0] * self.months
            month_min_dofs = [float("inf")] * self.months
            month_max_dofs = [-float("inf")] * self.months
            month_sout = [0] * self.months

            for t in range(n):
                dt = dates[t]
                month_key = dt.year * 12 + dt.month - self.month_index_base
                opening = stock

                if pending is not None and pending["arrival"] == dt:
                    received_qty = pending["fulfilled"]
                    stock += received_qty
                    if exp_short:
                        rem_shelf = int(rng.uniform(45, 150))
                    else:
                        rem_shelf = int(rng.uniform(0.3, 0.8) * com["shelf_life_days"])
                    expiry = dt + timedelta(days=rem_shelf)
                    manuf = expiry - timedelta(days=com["shelf_life_days"])
                    batches.append({
                        "batch_id": f"BAT{batch_seq + 1:07d}", "commodity_id": cid, "facility_id": fid,
                        "received_date": dt, "manufacturing_date": manuf, "expiry_date": expiry,
                        "initial_quantity": received_qty, "remaining_quantity": received_qty,
                        "status": "ACTIVE", "sequence": batch_seq + 1,
                    })
                    batch_seq += 1
                    actual_delivery = dt
                    expected_delivery = pending["expected_delivery"]
                    delay_days = max(0, (actual_delivery - expected_delivery).days)
                    self.shipments.append({
                        "shipment_id": f"SHP{shipment_seq + 1:07d}",
                        "order_id": pending["order_id"],
                        "origin_type": "WAREHOUSE",
                        "origin_id": pending["warehouse_id"],
                        "destination_type": "FACILITY",
                        "destination_id": fid,
                        "commodity_id": cid,
                        "quantity_shipped": received_qty,
                        "dispatch_date": pending["dispatch"].isoformat(),
                        "expected_arrival_date": expected_delivery.isoformat(),
                        "actual_arrival_date": actual_delivery.isoformat(),
                        "transport_status": "DELAYED" if delay_days > 0 else "DELIVERED",
                        "delay_days": delay_days,
                    })
                    shipment_seq += 1
                    pending["order"]["actual_delivery_date"] = actual_delivery.isoformat()
                    pending["order"]["quantity_fulfilled"] = received_qty
                    pending["order"]["_delivered"] = True
                    pending = None
                else:
                    received_qty = 0.0

                expiry_adj = 0.0
                still_active = []
                for b in batches:
                    if b["expiry_date"] <= dt and b["remaining_quantity"] > 0:
                        expiry_adj -= b["remaining_quantity"]
                        self.expired_units += b["remaining_quantity"]
                        b["remaining_quantity"] = 0.0
                        b["status"] = "EXPIRED"
                    if b["remaining_quantity"] > 0:
                        still_active.append(b)
                    else:
                        if b["status"] == "ACTIVE":
                            b["status"] = "FULLY_CONSUMED"
                        ended_batches.append(b)
                batches = still_active
                stock += expiry_adj

                demand_t = float(demand[t])
                issued = min(demand_t, stock)
                stock -= issued

                adjusted = expiry_adj
                if adj_mask[t] and stock > 0:
                    a = -min(adj_amt[t], stock)
                    stock += a
                    adjusted += a

                opening_r = round(float(opening), 1)
                received_r = round(float(received_qty), 1)
                issued_r = round(float(issued), 1)
                adjusted_r = round(float(adjusted), 1)
                closing_r = round(opening_r + received_r - issued_r + adjusted_r, 1)
                closing = max(0.0, closing_r)
                stock = closing

                avg_recent = max(expected, 1e-6)
                if closing <= 0.0:
                    status = "STOCKOUT"
                    self.stockout_days += 1
                    self.stockout_facility_commodity.add((fid, cid))
                elif closing < safety_level:
                    status = "CRITICAL"
                elif closing < min_scaled:
                    status = "LOW"
                elif closing > max_scaled * 1.05 or (closing / avg_recent) > 70.0:
                    status = "OVERSTOCKED"
                else:
                    status = "NORMAL"

                issued_from_batch = issued
                if issued_from_batch > 0:
                    for b in sorted(batches, key=lambda x: x["expiry_date"]):
                        if issued_from_batch <= 0:
                            break
                        take = min(b["remaining_quantity"], issued_from_batch)
                        b["remaining_quantity"] -= take
                        issued_from_batch -= take
                        if b["remaining_quantity"] <= 0:
                            b["remaining_quantity"] = 0.0
                            if b["status"] == "ACTIVE":
                                b["status"] = "FULLY_CONSUMED"

                if self.rng.random() < 0.003:
                    status = None

                inv_row = (dt.isoformat(), fid, cid, opening_r, received_r, issued_r, adjusted_r, closing, status)
                inv_w.add_row(inv_row)

                qc = float(round(float(issued), 1))
                pdi = float(round(demand_t / max(base * cf, 1e-9), 3))
                sf = float(round(sems[t], 3))
                ev_name = ev_names[t]
                dq_flag = "OK"
                if self.rng.random() < 0.004:
                    qc = None
                    dq_flag = "MISSING_VALUE"
                elif self.rng.random() < 0.01:
                    dq_flag = "DELAYED_REPORTING"
                con_row = (dt.isoformat(), fid, cid, qc, pdi, sf, ev_name, dq_flag)
                con_w.add_row(con_row)
                if dq_flag == "OK" and self.rng.random() < 0.00012 and len(dup_consumption) < 400:
                    dup_consumption.append(con_row)

                if pending is None and closing < reorder_point:
                    order_seq += 1
                    order_id = f"ORD{order_seq:07d}"
                    qty_raw = (max_scaled - closing) * order_factor
                    qty_ordered = max(pack, int(math.ceil(qty_raw / pack) * pack))
                    supplier_pool = CATEGORY_SUPPLIERS.get(com["category"], [])
                    if mode == "STRESS":
                        supplier_id = "SUP006" if fac["county"] not in ("Garissa",) else "SUP009"
                    else:
                        supplier_id = str(rng.choice(supplier_pool))
                    priority = "HIGH" if closing < safety_level else ("MEDIUM" if com["criticality_level"] in ("HIGH", "CRITICAL") else "LOW")
                    if priority == "HIGH":
                        self.emergency_orders += 1
                    processing = int(rng.integers(1, 3))
                    transit = max(1, lead - processing)
                    expected_delivery = dt + timedelta(days=lead)
                    sup = self.suppliers[supplier_id]
                    otd = sup[4]
                    if otd < rng.random() or mode == "STRESS":
                        delay = int(rng.lognormal(2.4, 0.5)) + 3
                    else:
                        delay = 0
                    if dt in self.disruption_days:
                        delay += int(rng.integers(10, 21))
                    dispatch = dt + timedelta(days=processing)
                    actual_arrival = dispatch + timedelta(days=transit + delay)
                    if rng.random() < 0.01:
                        cancelled = True
                        fulfilled = 0
                    else:
                        cancelled = False
                        fulfilled = qty_ordered
                        if rng.random() < 0.06:
                            fulfilled = max(pack, int(round(qty_ordered * 0.6 / pack) * pack))
                    self.orders.append({
                        "order_id": order_id,
                        "order_date": dt.isoformat(),
                        "ordering_organization": "FACILITY",
                        "facility_id": fid,
                        "warehouse_id": fac["primary_warehouse"],
                        "commodity_id": cid,
                        "quantity_ordered": qty_ordered,
                        "quantity_fulfilled": 0,
                        "order_status": "CANCELLED" if cancelled else "PENDING",
                        "expected_delivery_date": expected_delivery.isoformat(),
                        "actual_delivery_date": None,
                        "supplier_id": supplier_id,
                        "priority_level": priority,
                        "_delivered": False,
                        "_cancelled": cancelled,
                    })
                    if not cancelled:
                        pending = {
                            "order_id": order_id,
                            "warehouse_id": fac["primary_warehouse"],
                            "order": self.orders[-1],
                            "arrival": actual_arrival,
                            "expected_delivery": expected_delivery,
                            "dispatch": dispatch,
                            "fulfilled": fulfilled,
                        }

                month_close_end[month_key] = closing
                if closing > month_max_close[month_key]:
                    month_max_close[month_key] = closing
                dofs_today = closing / avg_recent
                if dofs_today < month_min_dofs[month_key]:
                    month_min_dofs[month_key] = dofs_today
                if dofs_today > month_max_dofs[month_key]:
                    month_max_dofs[month_key] = dofs_today
                if status == "STOCKOUT":
                    month_sout[month_key] += 1

            self.profiles[(cid, fid)] = [
                (month_end_dates[m], month_close_end[m], expected,
                 month_min_dofs[m], month_max_dofs[m], month_sout[m], month_max_close[m])
                for m in range(self.months)
            ]
            for b in batches + ended_batches:
                if b["remaining_quantity"] > 0 and b["status"] == "ACTIVE":
                    rem_days = (b["expiry_date"] - dates[-1]).days
                    if b["expiry_date"] <= dates[-1]:
                        b["status"] = "EXPIRED"
                        self.expired_units += b["remaining_quantity"]
                        b["remaining_quantity"] = 0.0
                    elif rem_days < max(60, int(0.3 * com["shelf_life_days"])):
                        b["status"] = "APPROACHING_EXPIRY"
                self.batches.append({
                    "batch_id": b["batch_id"], "commodity_id": b["commodity_id"], "facility_id": b["facility_id"],
                    "received_date": b["received_date"].isoformat(),
                    "manufacturing_date": b["manufacturing_date"].isoformat(),
                    "expiry_date": b["expiry_date"].isoformat(),
                    "initial_quantity": round(b["initial_quantity"], 1),
                    "remaining_quantity": round(b["remaining_quantity"], 1),
                    "batch_status": b["status"],
                })

        for r in dup_consumption:
            con_w.add_row(r)
        inv_w.close()
        con_w.close()
        self.orders_df = self._finalize_orders()

    def _finalize_orders(self):
        for o in self.orders:
            if o["_cancelled"]:
                o["order_status"] = "CANCELLED"
                o["actual_delivery_date"] = None
            elif not o["_delivered"]:
                o["order_status"] = "PENDING"
            else:
                exp = date.fromisoformat(o["expected_delivery_date"])
                act = date.fromisoformat(o["actual_delivery_date"])
                if o["quantity_fulfilled"] < o["quantity_ordered"]:
                    o["order_status"] = "PARTIALLY_FULFILLED"
                elif act > exp:
                    o["order_status"] = "DELAYED"
                else:
                    o["order_status"] = "FULFILLED"
        cols = ["order_id", "order_date", "ordering_organization", "facility_id", "warehouse_id",
                "commodity_id", "quantity_ordered", "quantity_fulfilled", "order_status",
                "expected_delivery_date", "actual_delivery_date", "supplier_id", "priority_level"]
        return pd.DataFrame([{k: o[k] for k in cols} for o in self.orders])

    def generate_redistribution(self):
        rng = self.rng
        rid = 0
        surplus_threshold = 45.0
        max_dist = 400.0
        for cid in [c["commodity_id"] for c in self.commodities]:
            com = self.commodities_by_id[cid]
            lead = com["lead_time_days"]
            safety_days = com["safety_stock_days"]
            pack = com["pack_size"]
            for m in range(self.months):
                srcs = []
                dests = []
                for f in self.facilities:
                    fid = f["facility_id"]
                    key = (cid, fid)
                    if key not in self.profiles:
                        continue
                    pl = self.profiles[key]
                    if m >= len(pl):
                        continue
                    dt, closing, expected, mn_dofs, mx_dofs, sout_days, mx_close = pl[m]
                    mx_releasable = mx_close - (safety_days + lead) * expected
                    need = max(0.0, (lead - min(mn_dofs, lead)) * expected)
                    if mx_dofs >= surplus_threshold and mx_releasable > 0:
                        srcs.append({"fid": fid, "closing": closing, "expected": expected,
                                     "dofs": mx_dofs, "releasable": mx_releasable, "date": dt})
                    if (mn_dofs < lead or sout_days > 0) and need > 0:
                        dests.append({"fid": fid, "closing": closing, "expected": expected,
                                      "dofs": mn_dofs, "need": need, "date": dt})
                for s in srcs:
                    sf = self.facilities_by_id[s["fid"]]
                    candidate_dests = []
                    for d in dests:
                        if s["fid"] == d["fid"]:
                            continue
                        df = self.facilities_by_id[d["fid"]]
                        dist = haversine_km(sf["latitude"], sf["longitude"], df["latitude"], df["longitude"])
                        candidate_dests.append((dist, d))
                    candidate_dests.sort(key=lambda x: x[0])
                    for dist, d in candidate_dests[:6]:
                        recommended = min(s["releasable"], d["need"])
                        recommended = float(math.ceil(recommended / pack) * pack)
                        if recommended > s["releasable"]:
                            recommended = float(int(s["releasable"] // pack) * pack)
                        if recommended <= 0:
                            continue
                        if dist <= max_dist:
                            status = "RECOMMENDED"
                            reason = "SURPLUS_TO_SHORTAGE_TRANSFER"
                        else:
                            status = "NOT_RECOMMENDED"
                            reason = "DISTANCE_TOO_LARGE"
                        rid += 1
                        transport_cost = round(dist * 45.0 + (recommended / pack) * 80.0, 2)
                        self.redis.append({
                            "redistribution_id": f"RED{rid:06d}",
                            "date": s["date"].isoformat(),
                            "commodity_id": cid,
                            "source_facility_id": s["fid"],
                            "destination_facility_id": d["fid"],
                            "quantity_available": round(s["releasable"], 1),
                            "quantity_requested": round(d["need"], 1),
                            "recommended_quantity": recommended,
                            "distance_km": round(dist, 1),
                            "transport_cost": transport_cost,
                            "source_days_of_stock": round(s["dofs"], 1),
                            "destination_days_of_stock": round(d["dofs"], 1),
                            "redistribution_status": status,
                            "recommendation_reason": reason,
                        })
        for cid in [c["commodity_id"] for c in self.commodities]:
            com = self.commodities_by_id[cid]
            lead = com["lead_time_days"]
            for m in range(0, self.months, 2):
                key = (cid, self.facilities[0]["facility_id"])
                if key not in self.profiles or m >= len(self.profiles[key]):
                    continue
                dt, _, _, _, _, _, _ = self.profiles[key][m]
                for i in range(0, min(len(self.facilities), 30), 6):
                    src = self.facilities[i]
                    dst = self.facilities[(i + 2) % min(len(self.facilities), 30)]
                    s_key = (cid, src["facility_id"])
                    d_key = (cid, dst["facility_id"])
                    if s_key not in self.profiles or d_key not in self.profiles:
                        continue
                    if m >= len(self.profiles[s_key]) or m >= len(self.profiles[d_key]):
                        continue
                    _, s_close, s_exp, _, _, _, _ = self.profiles[s_key][m]
                    _, d_close, d_exp, _, _, _, _ = self.profiles[d_key][m]
                    s_dofs = s_close / s_exp if s_exp > 0 else 0.0
                    d_dofs = d_close / d_exp if d_exp > 0 else 0.0
                    if s_dofs >= surplus_threshold and lead <= d_dofs < lead * 2:
                        rid += 1
                        sf = self.facilities_by_id[src["facility_id"]]
                        df = self.facilities_by_id[dst["facility_id"]]
                        dist = haversine_km(sf["latitude"], sf["longitude"], df["latitude"], df["longitude"])
                        releasable = s_close - (com["safety_stock_days"] + lead) * s_exp
                        self.redis.append({
                            "redistribution_id": f"RED{rid:06d}",
                            "date": dt.isoformat(),
                            "commodity_id": cid,
                            "source_facility_id": src["facility_id"],
                            "destination_facility_id": dst["facility_id"],
                            "quantity_available": round(max(0.0, releasable), 1),
                            "quantity_requested": 0.0,
                            "recommended_quantity": 0.0,
                            "distance_km": round(dist, 1),
                            "transport_cost": round(dist * 45.0, 2),
                            "source_days_of_stock": round(s_dofs, 1),
                            "destination_days_of_stock": round(d_dofs, 1),
                            "redistribution_status": "NOT_RECOMMENDED",
                            "recommendation_reason": "DESTINATION_NO_SHORTAGE",
                        })
        self.redis_df = pd.DataFrame(self.redis)

    def introduce_data_quality(self):
        fac_df = self.facilities_df
        fac_dup = fac_df.copy()
        if len(fac_dup) >= 3:
            fac_dup.loc[fac_dup.index[:3], "sub_county"] = None
        fac_df = fac_dup
        self.facilities_df = fac_df

        com_df = self.commodities_df.copy()
        case_issues = [1, 5, 12, 23, 37]
        for i, idx in enumerate(case_issues):
            if idx < len(com_df):
                com_df.loc[idx, "category"] = com_df.loc[idx, "category"].lower() + " "
        self.commodities_df = com_df

        wh_df = self.warehouses_df.copy()
        if len(wh_df) > 3:
            wh_df.loc[wh_df.index[3], "warehouse_name"] = wh_df.loc[wh_df.index[3], "warehouse_name"] + " "
        self.warehouses_df = wh_df

        self.dq_issues = [
            {"issue_id": "ISSUE001", "affected_table": "FACILITIES", "record_reference": "sub_county of first 3 facilities",
             "issue_type": "MISSING_VALUE", "severity": "LOW", "description": "Sub-county missing for 3 facility records.",
             "suggested_action": "Impute from county centroid or drop rows for geospatial analyses."},
            {"issue_id": "ISSUE002", "affected_table": "COMMODITIES", "record_reference": "category field rows 1,5,12,23,37",
             "issue_type": "INCORRECT_FORMATTING", "severity": "LOW", "description": "Category stored in mixed case with trailing spaces.",
             "suggested_action": "Normalise case and strip whitespace; map to canonical category."},
            {"issue_id": "ISSUE003", "affected_table": "KEMSA_WAREHOUSES", "record_reference": "WH004 name",
             "issue_type": "INCORRECT_FORMATTING", "severity": "LOW", "description": "Trailing space in warehouse_name.",
             "suggested_action": "Strip whitespace and de-duplicate master name."},
            {"issue_id": "ISSUE004", "affected_table": "CONSUMPTION", "record_reference": "~0.4% of rows",
             "issue_type": "MISSING_VALUE", "severity": "MEDIUM", "description": "quantity_consumed missing; flagged MISSING_VALUE.",
             "suggested_action": "Drop or impute using patient_demand_index and historical median."},
            {"issue_id": "ISSUE005", "affected_table": "CONSUMPTION", "record_reference": "~1.0% of rows",
             "issue_type": "DELAYED_REPORTING", "severity": "LOW", "description": "Rows flagged DELAYED_REPORTING (reporting lag).",
             "suggested_action": "Shift or weight rows when aggregating weekly/monthly totals."},
            {"issue_id": "ISSUE006", "affected_table": "CONSUMPTION", "record_reference": "up to 400 exact duplicate rows",
             "issue_type": "DUPLICATE_RECORDS", "severity": "MEDIUM", "description": "Exact duplicate consumption records.",
             "suggested_action": "De-duplicate on date + facility + commodity before aggregation."},
            {"issue_id": "ISSUE007", "affected_table": "INVENTORY", "record_reference": "~0.3% of rows",
             "issue_type": "MISSING_VALUE", "severity": "LOW", "description": "stock_status missing; values derivable from arithmetic.",
             "suggested_action": "Re-derive stock_status from opening/closing and levels."},
        ]

    def build_master_frames(self):
        self.facilities_df = pd.DataFrame([
            {k: f[k] for k in ["facility_id", "facility_name", "facility_type", "county", "sub_county",
                               "latitude", "longitude", "facility_level", "bed_capacity",
                               "average_daily_patient_visits", "facility_status"]}
            for f in self.facilities
        ])
        self.warehouses_df = pd.DataFrame([
            {"warehouse_id": w[0], "warehouse_name": w[1], "region": w[2], "county": w[3],
             "latitude": w[4][0], "longitude": w[4][1], "storage_capacity_units": w[5],
             "warehouse_status": "ACTIVE"}
            for w in self.warehouse_list
        ])
        self.commodities_df = pd.DataFrame([
            {k: c[k] for k in ["commodity_id", "commodity_name", "category", "dosage_form",
                               "unit_of_measure", "pack_size", "unit_cost", "lead_time_days",
                               "minimum_stock_level", "maximum_stock_level", "safety_stock_days",
                               "shelf_life_days", "criticality_level"]}
            for c in self.commodities
        ])
        self.suppliers_df = pd.DataFrame([
            {"supplier_id": s[0], "supplier_name": s[1], "supplier_category": s[2],
             "average_lead_time_days": s[3], "on_time_delivery_rate": s[4],
             "reliability_score": s[5], "supplier_status": "ACTIVE"}
            for s in SUPPLIERS
        ])
        self.events_df = pd.DataFrame(self.demand_events)
        self.batches_df = pd.DataFrame(self.batches)
        self.shipments_df = pd.DataFrame(self.shipments)
        self.redis_df = pd.DataFrame(self.redis)
        self.scenario_df = pd.DataFrame(self.scenario_labels)

    def write_outputs(self, output_dir, conn):
        for table, frame in [
            ("FACILITIES", self.facilities_df),
            ("KEMSA_WAREHOUSES", self.warehouses_df),
            ("COMMODITIES", self.commodities_df),
            ("SUPPLIERS", self.suppliers_df),
            ("ORDERS", self.orders_df),
            ("SHIPMENTS", self.shipments_df),
            ("BATCHES", self.batches_df),
            ("REDISTRIBUTION_EVENTS", self.redis_df),
            ("DEMAND_EVENTS", self.events_df),
            ("DATA_QUALITY_ISSUES", pd.DataFrame(self.dq_issues)),
            ("SCENARIO_LABELS", self.scenario_df),
        ]:
            frame.to_csv(os.path.join(output_dir, table + ".csv"), index=False)
            if conn is not None:
                frame.to_sql(table, conn, if_exists="replace", index=False)

    def _read_inventory(self):
        return pd.read_csv(os.path.join(self.output_dir, "INVENTORY.csv"), dtype={
            "opening_stock": float, "quantity_received": float, "quantity_issued": float,
            "quantity_adjusted": float, "closing_stock": float})

    def _read_consumption(self):
        return pd.read_csv(os.path.join(self.output_dir, "CONSUMPTION.csv"), dtype={
            "quantity_consumed": float, "patient_demand_index": float, "seasonality_factor": float})

    def summary(self):
        inv = self._read_inventory()
        con = self._read_consumption()
        stockouts = inv[inv["stock_status"] == "STOCKOUT"]
        overstock = inv[inv["stock_status"] == "OVERSTOCKED"]
        delayed = self.orders_df[self.orders_df["order_status"] == "DELAYED"]
        pending = self.orders_df[self.orders_df["order_status"] == "PENDING"]
        cancelled = self.orders_df[self.orders_df["order_status"] == "CANCELLED"]
        partial = self.orders_df[self.orders_df["order_status"] == "PARTIALLY_FULFILLED"]
        recommended = self.redis_df[self.redis_df["redistribution_status"] == "RECOMMENDED"]
        not_recommended = self.redis_df[self.redis_df["redistribution_status"] == "NOT_RECOMMENDED"]
        expired = self.batches_df[self.batches_df["batch_status"] == "EXPIRED"]
        lines = [
            f"Facilities: {len(self.facilities_df)}",
            f"Counties: {self.facilities_df['county'].nunique()}",
            f"Warehouses: {len(self.warehouses_df)}",
            f"Commodities: {len(self.commodities_df)}",
            f"Suppliers: {len(self.suppliers_df)}",
            f"Inventory records: {len(inv):,}",
            f"Consumption records: {len(con):,}",
            f"Orders: {len(self.orders_df):,}",
            f"Shipments: {len(self.shipments_df):,}",
            f"Batches: {len(self.batches_df):,}",
            f"Redistribution opportunities: {len(recommended):,}",
            "",
            "Scenario indicators:",
            f"  S1 Stockout days: {len(stockouts):,} (unique facility-commodity: {len(self.stockout_facility_commodity):,})",
            f"  S2 Overstocked records: {len(overstock):,}",
            f"  S3 Redistribution RECOMMENDED: {len(recommended):,} | NOT_RECOMMENDED: {len(not_recommended):,}",
            f"  S4 Expired batches: {len(expired):,} (units expired: {self.expired_units:,.0f})",
            f"  S5 Delayed orders: {len(delayed):,} | Pending: {len(pending):,} | Cancelled: {len(cancelled):,} | Partial: {len(partial):,}",
            f"  Emergency (HIGH priority) orders: {self.emergency_orders:,}",
        ]
        text = "\n".join(lines)
        print(text)
        return text

    def validate(self):
        results = []
        masters = {
            "FACILITIES": set(self.facilities_df["facility_id"]),
            "COMMODITIES": set(self.commodities_df["commodity_id"]),
            "WAREHOUSES": set(self.warehouses_df["warehouse_id"]),
            "SUPPLIERS": set(self.suppliers_df["supplier_id"]),
            "ORDERS": set(self.orders_df["order_id"]),
        }
        inv = self._read_inventory()
        con = self._read_consumption()
        ship = self.shipments_df
        batch = self.batches_df
        redis = self.redis_df
        orders = self.orders_df

        def check(name, ok, detail):
            results.append((name, ok, detail))

        bad_fk_inv_f = set(inv["facility_id"]) - masters["FACILITIES"]
        bad_fk_inv_c = set(inv["commodity_id"]) - masters["COMMODITIES"]
        check("INVENTORY FK facility_id", len(bad_fk_inv_f) == 0, f"{len(bad_fk_inv_f)} bad")
        check("INVENTORY FK commodity_id", len(bad_fk_inv_c) == 0, f"{len(bad_fk_inv_c)} bad")
        bad_fk_con_f = set(con["facility_id"]) - masters["FACILITIES"]
        bad_fk_con_c = set(con["commodity_id"]) - masters["COMMODITIES"]
        check("CONSUMPTION FK facility_id", len(bad_fk_con_f) == 0, f"{len(bad_fk_con_f)} bad")
        check("CONSUMPTION FK commodity_id", len(bad_fk_con_c) == 0, f"{len(bad_fk_con_c)} bad")
        bad_fk_o_w = set(orders["warehouse_id"]) - masters["WAREHOUSES"]
        bad_fk_o_s = set(orders["supplier_id"]) - masters["SUPPLIERS"]
        bad_fk_o_f = set(orders["facility_id"]) - masters["FACILITIES"]
        bad_fk_o_c = set(orders["commodity_id"]) - masters["COMMODITIES"]
        check("ORDERS FK warehouse/supplier/facility/commodity",
              len(bad_fk_o_w | bad_fk_o_s | bad_fk_o_f | bad_fk_o_c) == 0,
              f"{len(bad_fk_o_w)+len(bad_fk_o_s)+len(bad_fk_o_f)+len(bad_fk_o_c)} bad")
        bad_fk_sh_o = set(ship["order_id"]) - masters["ORDERS"]
        check("SHIPMENTS FK order_id", len(bad_fk_sh_o) == 0, f"{len(bad_fk_sh_o)} bad")
        bad_fk_b_c = set(batch["commodity_id"]) - masters["COMMODITIES"]
        bad_fk_b_f = set(batch["facility_id"]) - masters["FACILITIES"]
        check("BATCHES FK commodity/facility", len(bad_fk_b_c | bad_fk_b_f) == 0, f"{len(bad_fk_b_c)+len(bad_fk_b_f)} bad")
        bad_fk_r_c = set(redis["commodity_id"]) - masters["COMMODITIES"]
        bad_fk_r_s = set(redis["source_facility_id"]) - masters["FACILITIES"]
        bad_fk_r_d = set(redis["destination_facility_id"]) - masters["FACILITIES"]
        check("REDISTRIBUTION FK commodity/facilities",
              len(bad_fk_r_c | bad_fk_r_s | bad_fk_r_d) == 0, f"{len(bad_fk_r_c)+len(bad_fk_r_s)+len(bad_fk_r_d)} bad")

        neg_inv = (inv[["opening_stock", "closing_stock"]] < 0).sum().sum()
        check("No negative inventory", neg_inv == 0, f"{neg_inv} negative cells")

        bal = inv["closing_stock"] - (inv["opening_stock"] + inv["quantity_received"]
                                      - inv["quantity_issued"] + inv["quantity_adjusted"])
        bad_bal = int((bal.abs() > 0.05).sum())
        check("Inventory arithmetic consistent", bad_bal == 0, f"{bad_bal} inconsistent rows")

        ord_exp = pd.to_datetime(orders["expected_delivery_date"], errors="coerce")
        ord_act = pd.to_datetime(orders["actual_delivery_date"], errors="coerce")
        ord_dt = pd.to_datetime(orders["order_date"], errors="coerce")
        valid_act = ord_act.notna() & (ord_act < ord_dt)
        check("No delivery before order date", int(valid_act.sum()) == 0, f"{int(valid_act.sum())} bad")

        ship_d = pd.to_datetime(ship["dispatch_date"])
        ship_a = pd.to_datetime(ship["actual_arrival_date"])
        bad_ship = int((ship_a < ship_d).sum())
        check("Shipment arrival not before dispatch", bad_ship == 0, f"{bad_ship} bad")

        b_man = pd.to_datetime(batch["manufacturing_date"])
        b_exp = pd.to_datetime(batch["expiry_date"])
        b_rec = pd.to_datetime(batch["received_date"])
        bad_b = int((b_exp <= b_man).sum())
        check("Expiry after manufacturing", bad_b == 0, f"{bad_b} bad")
        bad_b2 = int((b_exp <= b_rec).sum())
        check("Expiry after received", bad_b2 == 0, f"{bad_b2} bad")

        rec = redis[redis["redistribution_status"] == "RECOMMENDED"]
        bad_r = int((rec["recommended_quantity"] > rec["quantity_available"]).sum())
        check("Redistribution within source availability", bad_r == 0, f"{bad_r} bad")

        self.validation_results = results
        print("\n" + "=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        critical = ["Inventory arithmetic consistent", "No negative inventory"]
        all_ok = True
        for name, ok, detail in results:
            mark = "PASS" if ok else "FAIL"
            if not ok:
                all_ok = False
            print(f"[{mark}] {name}: {detail}")
        if not all_ok:
            print("WARNING: validation failures found - inspect generated data.")
        return all_ok


def main():
    parser = argparse.ArgumentParser(description="Generate a synthetic healthcare supply-chain dataset.")
    parser.add_argument("--output-dir", default="output", help="Output directory (default: output)")
    parser.add_argument("--facilities", type=int, default=235, help="Number of facilities (default: 235 across 47 counties)")
    parser.add_argument("--commodities", type=int, default=45, help="Number of commodities (default: 45)")
    parser.add_argument("--months", type=int, default=24, help="Number of months (default: 24)")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed (default: 42)")
    parser.add_argument("--no-sqlite", action="store_true", help="Skip SQLite database creation")
    args = parser.parse_args()

    if args.facilities > 1000:
        args.facilities = 1000
    if args.commodities > 45:
        args.commodities = 45
    if args.months > 24:
        args.months = 24

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    conn = None
    if not args.no_sqlite:
        db_path = os.path.join(output_dir, "supply_chain.db")
        if os.path.exists(db_path):
            os.remove(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=MEMORY")
        conn.execute("PRAGMA synchronous=OFF")

    gen = SupplyChainGenerator(args.facilities, args.commodities, args.months, seed=args.seed)
    gen.generate_facilities()
    gen.generate_commodities()
    gen.generate_events()
    gen.assign_modes()
    print(f"Simulating {len(gen.pairs):,} facility-commodity pairs over {gen.n_days} days ...")
    gen.simulate(output_dir, conn)
    print("Generating redistribution events ...")
    gen.generate_redistribution()
    gen.build_master_frames()
    print("Introducing controlled data-quality issues ...")
    gen.introduce_data_quality()
    gen.write_outputs(output_dir, conn)
    gen.output_dir = output_dir
    if conn is not None:
        conn.commit()
        conn.close()
    print("\n" + "=" * 70)
    print("DATASET SUMMARY")
    print("=" * 70)
    gen.summary()
    gen.validate()


if __name__ == "__main__":
    main()
