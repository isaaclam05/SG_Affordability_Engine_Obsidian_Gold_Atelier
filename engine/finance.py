import json, sys, math
from pathlib import Path
RULES=json.loads((Path(__file__).resolve().parent.parent/'config'/'rules.json').read_text())

def number(d,k,lo=0,hi=100000000):
    v=d.get(k)
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:
        raise ValueError(f'{k} must be a number between {lo} and {hi}')
    return float(v)

def choice(d,k,allowed):
    v=d.get(k)
    if v not in allowed: raise ValueError(f'{k} must be one of {", ".join(map(str,allowed))}')
    return v

def payment(principal,annual,years):
    if principal<=0:return 0.
    n=round(years*12)
    if n<1:raise ValueError('Loan term must be at least one month')
    r=annual/1200
    return principal/n if r==0 else principal*r/(1-(1+r)**(-n))

def schedule(principal,annual,years):
    due=payment(principal,annual,years); r=annual/1200; remaining=principal; rows=[]; interest=0
    for month in range(1,round(years*12)+1):
        charge=remaining*r
        paid=min(due,remaining+charge)
        remaining=max(0,remaining+charge-paid)
        interest+=charge
        rows.append({'month':month,'payment':round(paid,2),'interest':round(charge,2),'principal':round(paid-charge,2),'balance':round(remaining,2)})
        if remaining<0.005:break
    return rows,interest

def bsd(value):
    remain=value; duty=0
    for band,rate in RULES['residential_bsd']:
        amount=remain if band is None else min(remain,band)
        duty+=amount*rate;remain-=amount
        if remain<=0:break
    return math.floor(duty)

def money(x):return round(x,2)

def property_calc(d):
    price=number(d,'price',10000,100000000); market=number(d,'marketValue',10000,100000000)
    income=number(d,'income',1,10000000); debts=number(d,'debts',0,1000000)
    annual=number(d,'interest',0,30); years=number(d,'years',1,35)
    age=number(d,'age',18,100); existing=int(number(d,'existingLoans',0,2))
    if existing!=number(d,'existingLoans',0,2):raise ValueError('existingLoans must be an integer')
    kind=choice(d,'propertyType',['hdb','private','ec'])
    residency=choice(d,'residency',['SC','SPR','FR'])
    owned=int(number(d,'ownedProperties',0,2))
    if owned!=number(d,'ownedProperties',0,2):raise ValueError('ownedProperties must be an integer')
    if kind=='hdb' and years>30:raise ValueError('HDB bank-loan tenure cannot exceed 30 years in this model')
    limit=RULES['property_ltv_first'] if existing==0 else RULES['property_ltv_second'] if existing==1 else RULES['property_ltv_third']
    reduced=(years>(25 if kind=='hdb' else 30) or age+years>65)
    if reduced:limit=max(0,limit-RULES['property_ltv_tenure_reduction'])
    collateral=min(price,market)
    loan_cap=collateral*limit
    tdsr_headroom=max(0,income*RULES['tdsr']-debts)
    msr_headroom=income*RULES['msr'] if kind in ('hdb','ec') else float('inf')
    max_monthly=min(tdsr_headroom,msr_headroom)
    # Assessment uses user-selected interest. Bank underwriting may require a higher stress rate.
    rate=annual/1200; months=round(years*12)
    affordable=max_monthly*months if rate==0 else max_monthly*(1-(1+rate)**(-months))/rate
    loan=min(loan_cap,affordable)
    monthly=payment(loan,annual,years)
    duty_value=max(price,market)
    absd_rate=RULES['absd'][residency][owned]
    duty=bsd(duty_value);absd=math.floor(duty_value*absd_rate)
    upfront=price-loan+duty+absd
    rows,interest_total=schedule(loan,annual,years)
    maintenance=number(d,'maintenance',0,100000)
    property_tax=number(d,'propertyTax',0,100000) if 'propertyTax' in d else 0
    home_insurance=number(d,'homeInsurance',0,100000) if 'homeInsurance' in d else 0
    utilities=number(d,'utilities',0,100000) if 'utilities' in d else 0
    monthly_running=maintenance+(property_tax+home_insurance)/12+utilities
    horizon=number(d,'horizon',1,50)
    horizon_months=round(horizon*12)
    interest_horizon=sum(r['interest'] for r in rows[:horizon_months])
    # Cash outflows, not net cost after sale. Excludes property appreciation and sale proceeds.
    cash_outflows=upfront+sum(r['payment'] for r in rows[:horizon_months])+monthly_running*horizon_months
    reasons=[]
    if affordable+0.01<loan_cap:reasons.append('Debt-servicing capacity limits the modelled loan.')
    if reduced:reasons.append('Long tenure or age beyond 65 reduces the modelled LTV limit.')
    if debts>=income*RULES['tdsr']:reasons.append('Existing debts exhaust the TDSR allowance.')
    reasons.append('Eligibility, CPF, minimum cash down payment, HDB rules, grants, loan stress rates and lender underwriting require separate assessment.')
    return {'kind':'property','rulesVersion':RULES['version'],'loan':money(loan),'ltvLimit':money(limit*100),'ltvLoanCap':money(loan_cap),'affordabilityLoanCap':money(affordable),'monthly':money(monthly),'monthlyRunning':money(monthly_running),'monthlyTotal':money(monthly+monthly_running),'incomeShare':money((monthly+monthly_running)/income*100),'remainingIncome':money(income-debts-monthly-monthly_running),'tdsrPercent':money((debts+monthly)/income*100),'msrPercent':money(monthly/income*100),'downPayment':money(price-loan),'bsd':duty,'absd':absd,'absdRate':money(absd_rate*100),'upfront':money(upfront),'totalInterest':money(interest_total),'horizonInterest':money(interest_horizon),'horizonOutflows':money(cash_outflows),'horizonYears':horizon,'remainingAtHorizon':rows[min(len(rows),horizon_months)-1]['balance'] if rows else 0,'schedule':rows,'notes':reasons,'status':'Within modelled debt and LTV limits' if loan>0 else 'Insufficient modelled debt capacity'}

def vehicle_calc(d):
    price=number(d,'price',1000,10000000);omv=number(d,'omv',0,10000000)
    income=number(d,'income',1,10000000); debts=number(d,'debts',0,1000000)
    annual=number(d,'interest',0,30);years=number(d,'years',1,7)
    down=number(d,'downPayment',0,10000000)
    if down>price:raise ValueError('Down payment cannot exceed vehicle price')
    ltv=RULES['car_ltv_low'] if omv<=RULES['car_omv_threshold'] else RULES['car_ltv_high']
    max_loan=price*ltv; requested=price-down
    loan=min(requested,max_loan)
    actual_down=price-loan
    finance_method=choice(d,'financeMethod',['reducing','flat']) if 'financeMethod' in d else 'reducing'
    if finance_method=='flat':
        months=round(years*12);flat_interest=loan*annual/100*years;monthly=(loan+flat_interest)/months if months else 0
        balance=loan;rows=[];interest=0
        for m in range(1,months+1):
            charge=flat_interest/months;principal_paid=min(balance,loan/months);balance=max(0,balance-principal_paid);interest+=charge
            rows.append({'month':m,'payment':money(principal_paid+charge),'principal':money(principal_paid),'interest':money(charge),'balance':money(balance)})
    else:
        monthly=payment(loan,annual,years);rows,interest=schedule(loan,annual,years)
    insurance=number(d,'insurance',0,100000);road=number(d,'roadTax',0,100000)
    fuel=number(d,'fuel',0,100000);parking=number(d,'parking',0,100000);maintenance=number(d,'maintenance',0,100000)
    property_tax=number(d,'propertyTax',0,100000) if 'propertyTax' in d else 0
    home_insurance=number(d,'homeInsurance',0,100000) if 'homeInsurance' in d else 0
    utilities=number(d,'utilities',0,100000) if 'utilities' in d else 0
    monthly_running=maintenance+(property_tax+home_insurance)/12+utilities
    erp=number(d,'erp',0,100000) if 'erp' in d else 0
    other=number(d,'otherRunning',0,100000) if 'otherRunning' in d else 0
    horizon=number(d,'horizon',1,20)
    months=round(horizon*12)
    recurring=(insurance+road)/12+fuel+parking+maintenance+erp+other
    outflows=actual_down+sum(r['payment'] for r in rows[:months])+recurring*months
    return {'kind':'vehicle','rulesVersion':RULES['version'],'loan':money(loan),'ltvLimit':money(ltv*100),'maxLoan':money(max_loan),'monthly':money(monthly),'monthlyTotal':money(monthly+recurring),'incomeShare':money((monthly+recurring)/income*100),'remainingIncome':money(income-debts-monthly-recurring),'financeMethod':finance_method,'downPayment':money(actual_down),'totalInterest':money(interest),'monthlyRunning':money(recurring),'horizonOutflows':money(outflows),'horizonYears':horizon,'remainingAtHorizon':rows[min(len(rows),months)-1]['balance'] if rows else 0,'schedule':rows,'status':'Within modelled vehicle financing limits','notes':['Financing method is an illustration; verify the bank or dealer offer and effective interest rate.','Vehicle price must include COE and applicable registration taxes. ARF, COE and rebates are not calculated separately.','Depreciation, resale proceeds, ERP and unexpected costs are excluded.','LTV and 7-year tenure model is for regulated individual motor-vehicle financing; other arrangements may differ.']}

def main():
    try:
        payload=json.load(sys.stdin)
        if not isinstance(payload,dict):raise ValueError('Expected JSON object')
        kind=payload.get('kind')
        if kind=='property':result=property_calc(payload)
        elif kind=='vehicle':result=vehicle_calc(payload)
        elif kind=='combined':
            prop=payload.get('property');vehicle=payload.get('vehicle')
            if not isinstance(prop,dict) or not isinstance(vehicle,dict):raise ValueError('Both property and vehicle inputs are required')
            prop=property_calc(prop);vehicle=vehicle_calc(vehicle)
            income=number(payload,'income',1,10000000);debts=number(payload,'debts',0,1000000)
            total=prop['monthlyTotal']+vehicle['monthlyTotal'];remaining=income-debts-total
            result={'kind':'combined','property':{'monthly':prop['monthly'],'running':prop['monthlyRunning'],'total':prop['monthlyTotal'],'upfront':prop['upfront'],'status':prop['status']},'vehicle':{'monthly':vehicle['monthly'],'running':vehicle['monthlyRunning'],'total':vehicle['monthlyTotal'],'upfront':vehicle['downPayment'],'status':vehicle['status']},'monthlyTotal':money(total),'incomeShare':money(total/income*100),'remainingIncome':money(remaining),'existingDebt':debts,'income':income,'rulesVersion':RULES['version'],'note':'Cash-flow planning only; combined scenario is not a lender approval or full eligibility check.'}
        else:raise ValueError('Unknown calculator type')
        print(json.dumps({'ok':True,'data':result},allow_nan=False))
    except (ValueError,KeyError,TypeError,OverflowError) as e:
        print(json.dumps({'ok':False,'error':str(e)}))
        sys.exit(2)
if __name__=='__main__':main()
