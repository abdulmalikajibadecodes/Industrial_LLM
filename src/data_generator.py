import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from faker import Faker
import json

fake = Faker()

# Equipment types and their common issues
EQUIPMENT_TYPES = {
    'pump': ['bearing_wear', 'seal_leak', 'cavitation', 'vibration', 'temperature_spike'],
    'motor': ['overheating', 'bearing_failure', 'winding_insulation', 'voltage_fluctuation'],
    'compressor': ['oil_leak', 'pressure_drop', 'valve_malfunction', 'cooling_issue'],
    'turbine': ['blade_erosion', 'bearing_wear', 'lubrication_issue', 'balance_problem'],
    'heat_exchanger': ['fouling', 'corrosion', 'thermal_stress', 'flow_restriction']
}

def generate_log_entry(equipment_id, equipment_type, timestamp, severity='INFO'):
    """Generate realistic industrial log entry"""
    
    issues = EQUIPMENT_TYPES[equipment_type]
    
    if severity == 'WARNING' or severity == 'ERROR':
        issue = random.choice(issues)
        
        templates = {
            'bearing_wear': f"{equipment_id}: Vibration levels elevated to {{vib}}Hz, potential bearing wear detected",
            'temperature_spike': f"{equipment_id}: Temperature reading {{temp}}°C exceeds normal range (40-60°C)",
            'seal_leak': f"{equipment_id}: Pressure drop detected, possible seal integrity compromise",
            'oil_leak': f"{equipment_id}: Oil level decreased by {{oil_loss}}L in last 24h cycle",
            'pressure_drop': f"{equipment_id}: System pressure dropped to {{pressure}} PSI, investigating cause"
        }
        
        # Add realistic values
        message = templates.get(issue, f"{equipment_id}: {issue.replace('_', ' ').title()} detected during routine check")
        message = message.format(
            vib=round(random.uniform(8.5, 12.0), 1),
            temp=round(random.uniform(75, 95), 1),
            oil_loss=round(random.uniform(0.5, 2.0), 1),
            pressure=round(random.uniform(15, 25), 1)
        )
    else:
        # Normal operational messages
        normal_messages = [
            f"{equipment_id}: Routine maintenance completed successfully",
            f"{equipment_id}: Operating within normal parameters",
            f"{equipment_id}: Scheduled inspection - no issues found",
            f"{equipment_id}: Performance metrics nominal"
        ]
        message = random.choice(normal_messages)
    
    return {
        'timestamp': timestamp.isoformat(),
        'equipment_id': equipment_id,
        'equipment_type': equipment_type,
        'severity': severity,
        'message': message,
        'facility': random.choice(['Plant_A', 'Plant_B', 'Plant_C']),
        'operator': fake.name()
    }

def generate_dataset(num_entries=1000):
    """Generate complete dataset"""
    
    logs = []
    
    # Generate equipment IDs
    equipment_list = []
    for eq_type in EQUIPMENT_TYPES.keys():
        for i in range(1, 6):  # 5 of each type
            equipment_list.append((f"{eq_type}_{i:02d}", eq_type))
    
    # Generate logs over 30 days
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(num_entries):
        # Random timestamp within 30 days
        random_hours = random.randint(0, 30*24)
        timestamp = start_date + timedelta(hours=random_hours)
        
        # Select random equipment
        equipment_id, equipment_type = random.choice(equipment_list)
        
        # Determine severity (80% INFO, 15% WARNING, 5% ERROR)
        severity = np.random.choice(['INFO', 'WARNING', 'ERROR'], p=[0.8, 0.15, 0.05])
        
        log_entry = generate_log_entry(equipment_id, equipment_type, timestamp, severity)
        logs.append(log_entry)
    
    return pd.DataFrame(logs).sort_values('timestamp')

# Generate and save data
if __name__ == "__main__":
    df = generate_dataset(4000)
    df.to_csv('industrial_logs.csv', index=False)
    df.to_json('industrial_logs.jsonl', orient='records', lines=True)
    print(f"Generated {len(df)} log entries")
    print(df.head())