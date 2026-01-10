def calculate_price(material, laser_time, labor, power, packaging, overhead, margin):
    base_cost = material + (laser_time * labor) + power + packaging + overhead
    final_price = base_cost * (1 + margin / 100)

    # Psychological pricing
    if final_price > 100:
        final_price = round(final_price / 10) * 10 - 1

    return round(final_price, 2)
