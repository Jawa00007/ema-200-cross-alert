//+------------------------------------------------------------------+
//| HawkSR_M15_M1_EA.mq5                                             |
//| Mechanical interpretation of supplied HawkTrading transcript.    |
//| M15 confirmed fractal levels; M1 reversal or direct breakout.      |
//+------------------------------------------------------------------+
#property strict
#property version "1.00"
#property description "M15 S/R + M1 confirmation. Demo-test before live use."
#include <Trade/Trade.mqh>
CTrade trade;

input string InpSymbol="";                       // Blank = chart symbol
input double InpRiskPercent=0.50;                // Equity risk per trade
input bool InpUseReversals=true;
input bool InpUseBreakout=true;
input int InpM15Lookback=160;
input int InpATRPeriod=14;
input double InpZoneATR=0.12;                    // M15 ATR fraction for level zone
input double InpSLBufferATR=0.08;                // M1 ATR fraction beyond swing
input double InpStrongBodyFraction=0.65;
input double InpMinRewardRisk=1.20;
input double InpMaxSpreadPoints=80;              // Calibrate to broker's XAUUSD quote
input int InpMaxTradesPerDay=3;
input int InpMaxConsecutiveLosses=2;
input double InpMaxDailyLossPercent=2.0;
input bool InpBreakEvenAtTP1=true;
input ulong InpMagic=151001;
input int InpDeviationPoints=20;

int hFractals=INVALID_HANDLE, hATR15=INVALID_HANDLE, hATR1=INVALID_HANDLE;
datetime lastM1Bar=0, dayStart=0, lastExitDealTime=0;
double dayStartEquity=0, activeTP1=0;
int tradesToday=0, consecutiveLosses=0;
bool tp1Done=false;

string Sym(){ return InpSymbol=="" ? _Symbol : InpSymbol; }
double Pt(){ return SymbolInfoDouble(Sym(),SYMBOL_POINT); }
double NP(double p){ return NormalizeDouble(p,(int)SymbolInfoInteger(Sym(),SYMBOL_DIGITS)); }
double ATR(int h,int shift=1){ double a[]; ArraySetAsSeries(a,true); if(h==INVALID_HANDLE||CopyBuffer(h,0,shift,1,a)!=1)return 0; return a[0]; }
bool NewM1(){ datetime t=iTime(Sym(),PERIOD_M1,0); if(t==0||t==lastM1Bar)return false; lastM1Bar=t; return true; }
datetime DayStart(){ MqlDateTime x; TimeToStruct(TimeCurrent(),x); x.hour=0;x.min=0;x.sec=0;return StructToTime(x); }
void DailyRefresh(){ datetime d=DayStart(); if(d!=dayStart){dayStart=d;dayStartEquity=AccountInfoDouble(ACCOUNT_EQUITY);tradesToday=0;consecutiveLosses=0;} }
bool RiskBlocked(){ DailyRefresh(); double eq=AccountInfoDouble(ACCOUNT_EQUITY); double loss=(dayStartEquity-eq)/MathMax(dayStartEquity,1.0)*100.0; return loss>=InpMaxDailyLossPercent||tradesToday>=InpMaxTradesPerDay||consecutiveLosses>=InpMaxConsecutiveLosses; }
bool HasPosition(){ for(int i=PositionsTotal()-1;i>=0;i--){ ulong t=PositionGetTicket(i); if(t==0)continue; if(PositionGetString(POSITION_SYMBOL)==Sym()&&(ulong)PositionGetInteger(POSITION_MAGIC)==InpMagic)return true;}return false; }
double SpreadPts(){ MqlTick t; if(!SymbolInfoTick(Sym(),t))return 1e9; return (t.ask-t.bid)/Pt(); }

bool Levels(double price,double &sup,double &res){
 sup=0;res=0; double up[],lo[]; ArraySetAsSeries(up,true);ArraySetAsSeries(lo,true);
 int n=MathMax(InpM15Lookback,40); if(CopyBuffer(hFractals,0,0,n,up)<n||CopyBuffer(hFractals,1,0,n,lo)<n)return false;
 // Fractals are confirmed with completed bars; search newest confirmed swing first.
 for(int i=3;i<n;i++){ if(sup==0&&lo[i]>0&&lo[i]<price)sup=lo[i]; if(res==0&&up[i]>0&&up[i]>price)res=up[i]; if(sup>0&&res>0)break; }
 return sup>0||res>0;
}
double SwingLow(double price){double s=0,r=0;Levels(price,s,r);return s;}
double SwingHigh(double price){double s=0,r=0;Levels(price,s,r);return r;}
double Body(const MqlRates &c){return MathAbs(c.close-c.open);}
double Range(const MqlRates &c){return MathMax(c.high-c.low,Pt());}
double LowerWick(const MqlRates &c){return MathMin(c.open,c.close)-c.low;}
double UpperWick(const MqlRates &c){return c.high-MathMax(c.open,c.close);}
bool Bull(const MqlRates &c){return c.close>c.open;}
bool Bear(const MqlRates &c){return c.close<c.open;}
bool StrongBull(const MqlRates &c){return Bull(c)&&Body(c)/Range(c)>=InpStrongBodyFraction;}
bool StrongBear(const MqlRates &c){return Bear(c)&&Body(c)/Range(c)>=InpStrongBodyFraction;}

double Lots(double entry,double sl){
 double money=AccountInfoDouble(ACCOUNT_EQUITY)*InpRiskPercent/100.0;
 double ts=SymbolInfoDouble(Sym(),SYMBOL_TRADE_TICK_SIZE), tv=SymbolInfoDouble(Sym(),SYMBOL_TRADE_TICK_VALUE_LOSS);
 if(tv<=0)tv=SymbolInfoDouble(Sym(),SYMBOL_TRADE_TICK_VALUE); if(ts<=0||tv<=0)return 0;
 double perLot=MathAbs(entry-sl)/ts*tv; if(perLot<=0)return 0;
 double step=SymbolInfoDouble(Sym(),SYMBOL_VOLUME_STEP),minv=SymbolInfoDouble(Sym(),SYMBOL_VOLUME_MIN),maxv=SymbolInfoDouble(Sym(),SYMBOL_VOLUME_MAX);
 if(step<=0)return 0; double v=MathFloor((money/perLot)/step)*step; v=MathMin(v,maxv); if(v<minv)return 0; return NormalizeDouble(v,step<0.01?3:2);
}

bool OpenTrade(bool buy,double swing,double tp1,double tp2){
 MqlTick q; if(!SymbolInfoTick(Sym(),q))return false; double entry=buy?q.ask:q.bid, a=ATR(hATR1);
 if(a<=0)return false; double sl=NP(buy?swing-a*InpSLBufferATR:swing+a*InpSLBufferATR); tp1=NP(tp1);tp2=NP(tp2);
 if((buy&&(sl>=entry||tp2<=entry))||(!buy&&(sl<=entry||tp2>=entry)))return false;
 double risk=MathAbs(entry-sl), reward=MathAbs(tp2-entry); if(risk<=0||reward/risk<InpMinRewardRisk)return false;
 double minDist=(double)SymbolInfoInteger(Sym(),SYMBOL_TRADE_STOPS_LEVEL)*Pt();
 if((buy&&(entry-sl<minDist||tp2-entry<minDist))||(!buy&&(sl-entry<minDist||entry-tp2<minDist)))return false;
 double vol=Lots(entry,sl);if(vol<=0){Print("Trade skipped: minimum lot would exceed risk budget.");return false;}
 trade.SetExpertMagicNumber(InpMagic);trade.SetDeviationInPoints(InpDeviationPoints);trade.SetTypeFillingBySymbol(Sym());
 bool ok=buy?trade.Buy(vol,Sym(),0,sl,tp2,"HawkSR buy"):trade.Sell(vol,Sym(),0,sl,tp2,"HawkSR sell");
 if(ok){tradesToday++;tp1Done=false;activeTP1=tp1;Print("Opened ",(buy?"BUY":"SELL")," volume=",vol," SL=",sl," TP1=",tp1," TP2=",tp2);}
 else Print("Order failed: ",trade.ResultRetcode()," ",trade.ResultRetcodeDescription()); return ok;
}

void ManagePosition(){
 for(int i=PositionsTotal()-1;i>=0;i--){ulong t=PositionGetTicket(i);if(t==0)continue;
  if(PositionGetString(POSITION_SYMBOL)!=Sym()||(ulong)PositionGetInteger(POSITION_MAGIC)!=InpMagic)continue;
  long type=PositionGetInteger(POSITION_TYPE);MqlTick q;if(!SymbolInfoTick(Sym(),q))return;
  double px=type==POSITION_TYPE_BUY?q.bid:q.ask;bool hit=type==POSITION_TYPE_BUY?px>=activeTP1:px<=activeTP1;
  if(!tp1Done&&activeTP1>0&&hit){
   double vol=PositionGetDouble(POSITION_VOLUME),step=SymbolInfoDouble(Sym(),SYMBOL_VOLUME_STEP),minv=SymbolInfoDouble(Sym(),SYMBOL_VOLUME_MIN);
   double closeVol=step>0?MathFloor((vol*0.5)/step)*step:0;
   if(closeVol>=minv&&vol-closeVol>=minv&&trade.PositionClosePartial(Sym(),closeVol)){
    tp1Done=true;if(InpBreakEvenAtTP1)trade.PositionModify(Sym(),NP(PositionGetDouble(POSITION_PRICE_OPEN)),PositionGetDouble(POSITION_TP));Print("TP1: partial close completed.");
   }else{tp1Done=true;if(InpBreakEvenAtTP1)trade.PositionModify(Sym(),NP(PositionGetDouble(POSITION_PRICE_OPEN)),PositionGetDouble(POSITION_TP));}
  }return;
 }
}

// Reversal: price touches/rejects a level on the REJECTION candle (p), and
// the NEXT candle (c) confirms by closing beyond p's body in the reversal
// direction. The touch/reject test and the SL both anchor to p (the candle
// that actually made the wick) - not to c - per the transcript: "SL goes a
// little below the wick IT left behind" (the rejection candle's wick).
void Reversal(const MqlRates &c,const MqlRates &p,double s,double r,double tol){
 if(InpUseReversals&&s>0){
  bool touch=p.low<=s+tol&&p.low>=s-2*tol;
  bool reject=LowerWick(p)>Body(p)*0.5||Bull(p);
  bool confirm=Bull(c)&&c.close>MathMax(p.open,p.close);
  if(touch&&reject&&confirm&&r>c.close){double t2=SwingHigh(r+tol);if(t2>r)OpenTrade(true,p.low,r,t2);}
 }
 if(InpUseReversals&&r>0){
  bool touch=p.high>=r-tol&&p.high<=r+2*tol;
  bool reject=UpperWick(p)>Body(p)*0.5||Bear(p);
  bool confirm=Bear(c)&&c.close<MathMin(p.open,p.close);
  if(touch&&reject&&confirm&&s<c.close){double t2=SwingLow(s-tol);if(t2>0&&t2<s)OpenTrade(false,p.high,s,t2);}
 }
}

// Breakout: a strong/powerful (large-body) candle closes beyond a level -
// entry happens immediately on that candle's close, per the transcript
// ("powerful candle breaks it... entry will happen on this very candle").
// No waiting for a post-break pullback/retest.
void Breakout(const MqlRates &c,double s,double r,double tol){
 if(!InpUseBreakout)return;
 if(r>0&&StrongBull(c)&&c.close>r+tol){
  double t1=SwingHigh(r+tol); if(t1>c.close){double t2=SwingHigh(t1+tol); if(t2>t1)OpenTrade(true,c.low,t1,t2);}
 }
 else if(s>0&&StrongBear(c)&&c.close<s-tol){
  double t1=SwingLow(s-tol); if(t1>0&&t1<c.close){double t2=SwingLow(t1-tol); if(t2>0&&t2<t1)OpenTrade(false,c.high,t1,t2);}
 }
}

int OnInit(){
 if(!SymbolSelect(Sym(),true))return INIT_FAILED;
 hFractals=iFractals(Sym(),PERIOD_M15);hATR15=iATR(Sym(),PERIOD_M15,InpATRPeriod);hATR1=iATR(Sym(),PERIOD_M1,InpATRPeriod);
 if(hFractals==INVALID_HANDLE||hATR15==INVALID_HANDLE||hATR1==INVALID_HANDLE)return INIT_FAILED;
 trade.SetExpertMagicNumber(InpMagic);trade.SetDeviationInPoints(InpDeviationPoints);DailyRefresh();lastM1Bar=iTime(Sym(),PERIOD_M1,0);return INIT_SUCCEEDED;
}
void OnDeinit(const int reason){if(hFractals!=INVALID_HANDLE)IndicatorRelease(hFractals);if(hATR15!=INVALID_HANDLE)IndicatorRelease(hATR15);if(hATR1!=INVALID_HANDLE)IndicatorRelease(hATR1);}
void OnTick(){
 DailyRefresh();ManagePosition();if(!NewM1())return;if(RiskBlocked()||HasPosition()||SpreadPts()>InpMaxSpreadPoints)return;
 MqlRates a[];ArraySetAsSeries(a,true);if(CopyRates(Sym(),PERIOD_M1,0,4,a)<4)return;
 // Anchor level lookup to the candle before the signal candle so a fresh
 // breakout can still reference the level it has just crossed.
 double refPrice=a[2].close,s=0,r=0;if(!Levels(refPrice,s,r))return;
 double atr=ATR(hATR15);if(atr<=0)return;double tol=atr*InpZoneATR;
 Breakout(a[1],s,r,tol);if(!HasPosition())Reversal(a[1],a[2],s,r,tol);
}
void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &request,const MqlTradeResult &result){
 if(trans.type!=TRADE_TRANSACTION_DEAL_ADD||trans.deal==0||!HistoryDealSelect(trans.deal))return;
 if(HistoryDealGetString(trans.deal,DEAL_SYMBOL)!=Sym()||(ulong)HistoryDealGetInteger(trans.deal,DEAL_MAGIC)!=InpMagic)return;
 long e=HistoryDealGetInteger(trans.deal,DEAL_ENTRY);if(e!=DEAL_ENTRY_OUT&&e!=DEAL_ENTRY_OUT_BY)return;
 datetime tm=(datetime)HistoryDealGetInteger(trans.deal,DEAL_TIME);if(tm==lastExitDealTime)return;lastExitDealTime=tm;
 double pnl=HistoryDealGetDouble(trans.deal,DEAL_PROFIT)+HistoryDealGetDouble(trans.deal,DEAL_SWAP)+HistoryDealGetDouble(trans.deal,DEAL_COMMISSION);
 if(pnl<0)consecutiveLosses++;else if(pnl>0)consecutiveLosses=0;
}
//+------------------------------------------------------------------+
