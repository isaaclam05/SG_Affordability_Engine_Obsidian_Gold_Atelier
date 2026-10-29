import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'engine'))
from finance import bsd,payment,property_calc,vehicle_calc
class FinanceTests(unittest.TestCase):
 def test_bsd_bands(self):
  self.assertEqual(bsd(180000),1800)
  self.assertEqual(bsd(360000),5400)
  self.assertEqual(bsd(1000000),24600)
  self.assertEqual(bsd(4500100),209606)
 def test_zero_interest(self):self.assertAlmostEqual(payment(120000,0,10),1000)
 def test_property(self):
  r=property_calc(dict(price=850000,marketValue=850000,income=11000,debts=800,interest=4,years=25,age=30,existingLoans=0,propertyType='hdb',residency='SC',ownedProperties=0,maintenance=500,horizon=10))
  self.assertLessEqual(r['loan'],850000*.75)
  self.assertLessEqual(r['tdsrPercent'],55.01)
  self.assertLessEqual(r['msrPercent'],30.01)
  self.assertEqual(r['absd'],0)
  self.assertEqual(r['schedule'][-1]['balance'],0)
 def test_vehicle(self):
  r=vehicle_calc(dict(price=160000,omv=25000,income=8000,debts=700,interest=3.5,years=7,downPayment=65000,insurance=1800,roadTax=1000,fuel=250,parking=180,maintenance=150,horizon=7))
  self.assertEqual(r['loan'],95000)
  self.assertEqual(r['ltvLimit'],60)
  self.assertEqual(r['schedule'][-1]['balance'],0)
 def test_vehicle_ltv_caps(self):
  r=vehicle_calc(dict(price=100000,omv=30000,income=8000,debts=0,interest=0,years=5,downPayment=10000,insurance=0,roadTax=0,fuel=0,parking=0,maintenance=0,horizon=5))
  self.assertEqual(r['loan'],60000)
  self.assertEqual(r['downPayment'],40000)
if __name__=='__main__':unittest.main()
