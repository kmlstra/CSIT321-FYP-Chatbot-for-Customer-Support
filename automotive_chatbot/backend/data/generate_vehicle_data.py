import pandas as pd
import random
from datetime import datetime, timedelta

# Generate comprehensive vehicle data for Singapore market
def generate_vehicle_data():
    brands = ['Toyota', 'Honda', 'BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'Nissan', 'Mazda', 'Hyundai', 'Kia', 'Lexus', 'Infiniti', 'Subaru', 'Mitsubishi', 'Peugeot']
    
    # Brand-specific models
    brand_models = {
        'Toyota': ['Camry', 'Corolla', 'Prius', 'Alphard', 'Vellfire', 'C-HR', 'RAV4', 'Harrier', 'Sienta', 'Vios'],
        'Honda': ['Civic', 'Accord', 'CR-V', 'HR-V', 'City', 'Jazz', 'Odyssey', 'Shuttle', 'Freed'],
        'BMW': ['3 Series', '5 Series', 'X1', 'X3', 'X5', 'X7', '1 Series', '2 Series', 'i3', 'iX3'],
        'Mercedes-Benz': ['C-Class', 'E-Class', 'S-Class', 'GLA', 'GLC', 'GLE', 'GLS', 'A-Class', 'B-Class', 'CLA'],
        'Audi': ['A3', 'A4', 'A6', 'Q2', 'Q3', 'Q5', 'Q7', 'Q8', 'e-tron', 'TT'],
        'Volkswagen': ['Golf', 'Polo', 'Passat', 'Tiguan', 'Touran', 'Arteon', 'ID.4', 'ID.3'],
        'Nissan': ['Almera', 'Sylphy', 'Teana', 'X-Trail', 'Qashqai', 'Serena', 'Leaf', 'e-NV200'],
        'Mazda': ['3', '6', 'CX-3', 'CX-5', 'CX-8', 'CX-9', 'MX-5', 'Biante'],
        'Hyundai': ['Elantra', 'Sonata', 'Tucson', 'Santa Fe', 'i30', 'Kona', 'Ioniq', 'Staria'],
        'Kia': ['Cerato', 'Optima', 'Sportage', 'Sorento', 'Picanto', 'Rio', 'Stinger', 'EV6'],
        'Lexus': ['ES', 'GS', 'LS', 'NX', 'RX', 'GX', 'LX', 'IS', 'RC', 'UX'],
        'Infiniti': ['Q30', 'Q50', 'Q60', 'QX30', 'QX50', 'QX60', 'QX70', 'QX80'],
        'Subaru': ['Impreza', 'Legacy', 'Outback', 'XV', 'Forester', 'Ascent', 'WRX', 'BRZ'],
        'Mitsubishi': ['Lancer', 'Attrage', 'ASX', 'Outlander', 'Pajero', 'Eclipse Cross', 'Triton'],
        'Peugeot': ['208', '308', '508', '2008', '3008', '5008', 'Partner', 'Expert']
    }
    
    fuel_types = ['Petrol', 'Hybrid', 'Electric', 'Diesel']
    transmissions = ['Manual', 'Automatic', 'CVT', '7-Speed DCT', '8-Speed Auto', '9-Speed Auto']
    vehicle_types = ['Sedan', 'Hatchback', 'SUV', 'MPV', 'Coupe', 'Convertible', 'Wagon', 'Crossover']
    
    data = []
    
    for i in range(120):  # Generate 120 records
        brand = random.choice(brands)
        model = random.choice(brand_models[brand])
        
        # Determine COE category based on typical specifications
        is_luxury = brand in ['BMW', 'Mercedes-Benz', 'Audi', 'Lexus', 'Infiniti']
        is_large_suv = model in ['Alphard', 'Vellfire', 'X5', 'X7', 'GLE', 'GLS', 'Q7', 'Q8', 'Santa Fe', 'Sorento', 'RX', 'GX', 'LX', 'QX60', 'QX70', 'QX80', 'Outlander', 'Pajero']
        
        if is_luxury or is_large_suv or random.random() > 0.6:
            coe_category = 'B'
            engine_capacity = random.randint(1600, 4000)
            power = random.randint(130, 400)
            price_base = random.randint(90000, 250000)
        else:
            coe_category = 'A'
            engine_capacity = random.randint(1000, 1600)
            power = random.randint(80, 130)
            price_base = random.randint(60000, 120000)
        
        # Generate registration date (last 10 years)
        reg_date = datetime.now() - timedelta(days=random.randint(0, 3650))
        coe_expiry = reg_date + timedelta(days=3650)  # 10 years from registration
        coe_left = max(0, (coe_expiry - datetime.now()).days)
        
        # Calculate depreciation
        years_old = (datetime.now() - reg_date).days / 365.25
        depreciation_rate = min(0.7, years_old * 0.08)  # Max 70% depreciation
        current_price = int(price_base * (1 - depreciation_rate))
        
        # Mileage based on age
        annual_mileage = random.randint(8000, 25000)
        total_mileage = int(years_old * annual_mileage)
        
        # Road tax based on engine capacity
        if engine_capacity <= 1000:
            road_tax = 372
        elif engine_capacity <= 1600:
            road_tax = 744
        elif engine_capacity <= 3000:
            road_tax = 744 + ((engine_capacity - 1600) // 200) * 144
        else:
            road_tax = 744 + ((3000 - 1600) // 200) * 144 + ((engine_capacity - 3000) // 200) * 180
        
        # COE value based on category and time left
        if coe_category == 'A':
            coe_value = max(5000, 96999 * (coe_left / 3650))
        else:
            coe_value = max(5000, 113000 * (coe_left / 3650))
        
        fuel_type = random.choice(fuel_types)
        if fuel_type == 'Electric':
            engine_capacity = 0
            
        vehicle_data = {
            'Brand': brand,
            'Model': model,
            'Price': current_price,
            'Original_Price': price_base,
            'Depreciation_Rate': f"{depreciation_rate:.1%}",
            'Mileage': total_mileage,
            'Road_Tax': road_tax,
            'COE_Category': coe_category,
            'COE_Value': int(coe_value),
            'Registration_Date': reg_date.strftime('%Y-%m-%d'),
            'COE_Days_Left': coe_left,
            'Manufactured_Year': reg_date.year,
            'Transmission': random.choice(transmissions),
            'Fuel_Type': fuel_type,
            'Engine_Capacity': engine_capacity,
            'Power_HP': power,
            'Weight_KG': random.randint(1200, 2500),
            'Vehicle_Type': random.choice(vehicle_types),
            'Seating_Capacity': random.choice([2, 4, 5, 7, 8]),
            'Fuel_Economy_L100KM': round(random.uniform(4.5, 12.0), 1),
            'Top_Speed_KMH': random.randint(160, 280),
            'Acceleration_0_100': round(random.uniform(6.0, 12.0), 1),
            'Warranty_Years': random.choice([3, 5, 7]),
            'Safety_Rating': random.choice(['4 Star', '5 Star']),
            'Insurance_Group': random.randint(15, 50),
            'Dealer_Location': random.choice(['Toa Payoh', 'Jurong', 'Woodlands', 'Tampines', 'Orchard', 'Marina Bay']),
            'Service_Interval_KM': random.choice([5000, 10000, 15000]),
            'Availability': random.choice(['In Stock', 'Order Only', 'Limited Stock']),
            'Promotion': random.choice(['', 'Free 2 Years Warranty', 'Cash Rebate $5000', 'Free Insurance', 'Trade-in Bonus']),
            'Features': random.choice([
                'Sunroof, Leather Seats, Navigation',
                'Reverse Camera, Keyless Entry, Bluetooth',
                'Premium Audio, Heated Seats, LED Lights',
                '360 Camera, Wireless Charging, Ambient Lighting',
                'Autopilot, Massage Seats, Premium Sound'
            ])
        }
        
        data.append(vehicle_data)
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    # Generate and save the data
    df = generate_vehicle_data()
    df.to_excel('singapore_vehicle_data.xlsx', index=False)
    print(f"Generated {len(df)} vehicle records and saved to singapore_vehicle_data.xlsx")
    print("Sample data:")
    print(df.head()) 