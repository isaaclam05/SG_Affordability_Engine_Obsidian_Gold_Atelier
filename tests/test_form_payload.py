import json, subprocess, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
BASE={"kind":"property","price":500000,"marketValue":500000,"income":5000,"debts":0,"interest":3.5,"years":25,"age":25,"existingLoans":0,"propertyType":"hdb","residency":"SC","ownedProperties":0,"propertyTax":600,"homeInsurance":240,"utilities":200,"maintenance":100,"horizon":10}
class FormPayloadTests(unittest.TestCase):
    def test_property_dropdown_options(self):
        for existing in (0,1,2):
            for owned in (0,1,2):
                payload={**BASE,"existingLoans":existing,"ownedProperties":owned}
                result=subprocess.run(['python3',str(ROOT/'engine/finance.py')],input=json.dumps(payload),capture_output=True,text=True)
                data=json.loads(result.stdout)
                self.assertTrue(data['ok'],str(data))
                self.assertGreaterEqual(data['data']['monthlyTotal'],0)
    def test_string_dropdown_values_are_invalid_at_engine_boundary(self):
        payload={**BASE,"existingLoans":"0"}
        result=subprocess.run(['python3',str(ROOT/'engine/finance.py')],input=json.dumps(payload),capture_output=True,text=True)
        self.assertFalse(json.loads(result.stdout)['ok'])
if __name__=='__main__': unittest.main()
