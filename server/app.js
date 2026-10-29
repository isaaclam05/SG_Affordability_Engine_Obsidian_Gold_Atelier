const express=require('express');
const helmet=require('helmet');
const {rateLimit}=require('express-rate-limit');
const {spawn}=require('node:child_process');
const path=require('node:path');
const app=express();
app.disable('x-powered-by');
app.use(helmet({contentSecurityPolicy:{directives:{defaultSrc:["'self'"],scriptSrc:["'self'",'https://cdn.jsdelivr.net'],styleSrc:["'self'",'https://fonts.googleapis.com'],fontSrc:["'self'",'https://fonts.gstatic.com'],imgSrc:["'self'",'data:'],connectSrc:["'self'"]}}}));
app.use(express.json({limit:'16kb',strict:true}));
app.use('/api',rateLimit({windowMs:60_000,limit:50,standardHeaders:'draft-7',legacyHeaders:false}));

const COE_RESOURCE='d_69b3380ad7e51aff3a7dcc84eba52b8a';
let coeCache=null;
app.get('/api/coe',async(req,res)=>{
  if(coeCache && Date.now()-coeCache.at<6*60*60*1000)return res.json({ok:true,...coeCache.data,cached:true});
  try{
    const url=new URL('https://data.gov.sg/api/action/datastore_search');
    url.searchParams.set('resource_id',COE_RESOURCE);
    url.searchParams.set('limit','100');
    url.searchParams.set('sort','month desc,bidding_no desc');
    const response=await fetch(url,{signal:AbortSignal.timeout(9000)});
    if(!response.ok)throw new Error('Upstream HTTP '+response.status);
    const payload=await response.json();
    if(payload.success===false)throw new Error('Upstream API reported failure');
    const records=payload.result?.records||payload.data?.records||[];
    const valid=records.map(row=>({month:String(row.month||row.Month||''),round:Number(row.bidding_no||row['Bidding No']),category:String(row.vehicle_class||row['Vehicle Class']||''),premium:Number(String(row.premium||row.Premium||'').replace(/,/g,''))})).filter(r=>/^20\d\d-\d\d$/.test(r.month)&&[1,2].includes(r.round)&&/^Category [A-E]$/.test(r.category)&&Number.isFinite(r.premium)&&r.premium>0);
    valid.sort((a,b)=>b.month.localeCompare(a.month)||b.round-a.round);
    if(!valid.length)throw new Error('No valid COE data returned');
    const latest=valid[0];const prices={};
    for(const row of valid.filter(r=>r.month===latest.month&&r.round===latest.round))prices[row.category.slice(-1)]=row.premium;
    if(!prices.A||!prices.B)throw new Error('Incomplete latest COE categories');
    const data={prices,month:latest.month,biddingRound:latest.round,source:'LTA via data.gov.sg',sourceUrl:'https://data.gov.sg/datasets/'+COE_RESOURCE+'/view',retrievedAt:new Date().toISOString()};
    coeCache={at:Date.now(),data};res.json({ok:true,...data,cached:false});
  }catch(err){if(coeCache)return res.json({ok:true,...coeCache.data,cached:true,stale:true});res.status(503).json({ok:false,error:'Official COE prices are currently unavailable. Enter a manual premium or use a COE-inclusive price.'});}
});
app.get('/api/health',(req,res)=>res.json({ok:true,service:'SG Affordability Engine',timestamp:new Date().toISOString()}));
function calculate(input){return new Promise((resolve,reject)=>{
  const python=spawn(process.env.PYTHON_BIN||'python3',[path.join(__dirname,'../engine/finance.py')],{stdio:['pipe','pipe','pipe']});
  let stdout='',stderr='',settled=false;
  const timeout=setTimeout(()=>{python.kill('SIGKILL');finish(new Error('Calculation timed out'));},8000);
  function finish(error,value){if(settled)return;settled=true;clearTimeout(timeout);error?reject(error):resolve(value);}
  python.stdout.on('data',chunk=>{stdout+=chunk.toString();if(stdout.length>2_000_000){python.kill('SIGKILL');finish(new Error('Calculation output too large'));}});
  python.stderr.on('data',chunk=>{stderr+=chunk.toString().slice(0,500);});
  python.on('error',e=>finish(new Error('Python engine could not start: '+e.message)));
  python.on('close',code=>{if(settled)return;try{const data=JSON.parse(stdout);if(!data.ok)return finish(Object.assign(new Error(data.error),{status:400}));if(code!==0)return finish(new Error('Engine returned an error'));finish(null,data.data);}catch(e){finish(new Error('Invalid engine response'));}});
  python.stdin.on('error',()=>{});
  python.stdin.end(JSON.stringify(input));
});}
app.post('/api/calculate',async(req,res,next)=>{
 try{
  const input=req.body;
  if(!input||typeof input!=='object'||Array.isArray(input)||!['property','vehicle','combined'].includes(input.kind))return res.status(400).json({ok:false,error:'Invalid calculator request'});
  const result=await calculate(input);res.json({ok:true,data:result});
 }catch(e){next(e);}
});
app.use(express.static(path.join(__dirname,'../public'),{extensions:['html'],maxAge:process.env.NODE_ENV==='production'?'1h':0}));
app.use('/api',(req,res)=>res.status(404).json({ok:false,error:'API route not found'}));
app.use((err,req,res,next)=>{if(err instanceof SyntaxError&&'body' in err)return res.status(400).json({ok:false,error:'Invalid JSON'});const status=err.status||500;if(status>=500)console.error(err);res.status(status).json({ok:false,error:status>=500?'Calculation unavailable. Please try again.':err.message});});
if(require.main===module){const port=Number(process.env.PORT)||3000;app.listen(port,'0.0.0.0',()=>console.log(`SG Affordability Engine listening on ${port}`));}
module.exports=app;
