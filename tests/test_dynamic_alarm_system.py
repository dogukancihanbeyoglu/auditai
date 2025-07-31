#!/usr/bin/env python3
"""
Test script for dynamic alarm system
Creates a sample alarm using the new dynamic detection system
"""

from app import app, db
from models import AuditRule, AuditArea, DataSource, User
from services.ai_rule_engine import create_alarm, detect_data_source_info
from datetime import datetime

def test_dynamic_alarm_creation():
    """Test creating alarms with dynamic data source detection"""
    
    with app.app_context():
        # Find an existing rule and data source for testing
        rule = AuditRule.query.first()
        if not rule:
            print("No rules found for testing")
            return
            
        print(f"Testing with rule: {rule.name}")
        print(f"Rule type: {rule.rule_type}")
        print(f"Algorithm: {rule.algorithm}")
        
        # Test alarm data with various scenarios
        test_scenarios = [
            {
                'name': 'Financial Anomaly',
                'alarm_data': {
                    'title': 'Test Finansal Anomali',
                    'message': 'Dinamik sistem testi',
                    'severity': 'high',
                    'data': {
                        'detection_type': 'anomaly',
                        'anomaly_data': {
                            'record_index': 12345,
                            'score': 0.95,
                            'transaction_id': 'TXN_TEST_001',
                            'account': 'ACC_999',
                            'amount': 250000,
                            'features': ['amount', 'timestamp']
                        }
                    },
                    'confidence_score': 0.92
                }
            },
            {
                'name': 'HR Security Alert', 
                'alarm_data': {
                    'title': 'Test Personel Güvenlik Alarmı',
                    'message': 'Dinamik HR sistemi testi',
                    'severity': 'critical',
                    'data': {
                        'detection_type': 'security',
                        'violation_data': {
                            'id': 5678,
                            'employee_id': 'EMP_999',
                            'access_attempt': 'unauthorized',
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    },
                    'confidence_score': 0.88
                }
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n=== Testing: {scenario['name']} ===")
            
            # Test data source info detection
            source_info = detect_data_source_info(rule, scenario['alarm_data'])
            print(f"Detected source info: {source_info}")
            
            # Create alarm using dynamic system
            alarm = create_alarm(rule, scenario['alarm_data'])
            
            if alarm:
                print(f"✓ Created alarm #{alarm.id}")
                print(f"  Title: {alarm.title}")
                print(f"  Table: {alarm.source_data_info.get('table_name', 'N/A')}")
                print(f"  Schema: {alarm.source_data_info.get('schema_name', 'N/A')}")
                print(f"  Affected records: {len(alarm.affected_records) if alarm.affected_records else 0}")
                
                # Show affected record details
                if alarm.affected_records:
                    record = alarm.affected_records[0]
                    print(f"  First record ID: {record.get('record_id', 'N/A')}")
                    print(f"  Query info: {record.get('query_info', {}).get('suggested_query', 'N/A')}")
            else:
                print("✗ Failed to create alarm")

if __name__ == "__main__":
    test_dynamic_alarm_creation()