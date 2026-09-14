/* SMCPE dashboard i18n — FULL coverage. Shared key smcpe-lang with landing. Arabic-first default. */
const SMCPE_DASH_I18N = {
en:{
"nav_operate":"Operate","nav_compliance":"Compliance","nav_admin":"Admin","nav_dashboard":"Dashboard","nav_employees":"Employees","nav_run":"Payroll Run","nav_payslips":"Payslips","nav_fx":"FX Rates","nav_reports":"Reports","nav_bank":"Bank Export","nav_tenants":"Tenants & Users","nav_audit":"Audit Log","nav_settings":"Statutory Tables",
"top_period":"Payroll period","top_new":"New run","top_site":"Website","search_ph":"Search name, ID, national ID, bank…","btn_import":"Import CSV","btn_add":"Add employee","btn_approve":"Approve","btn_export":"Export","btn_download":"Download file","btn_send":"Send",
"ov_eb":"Nile Agro Trading · 2026-09","ov_title":"Payroll overview","ov_lede":"Period status, balances and pending items. This console is operational only.",
"kpi_head":"Headcount","kpi_head_s":"3 currencies · 3 NSIF warnings","kpi_gross":"Gross SDG","kpi_gross_s":"FX locked 25 Sep 09:00","kpi_nsif":"NSIF 25%","kpi_nsif_s":"Emp 8% + Co 17%","kpi_net":"Net SDG","kpi_net_s":"Awaiting approval",
"trace_title":"Calculation trace · one employee","pend_title":"Pending items",
"al1t":"3 contracts lack NSIF flag","al1d":"Review before posting.","al2t":"Zakat nisab changed","al2d":"Re-validate 2 staff.","al3t":"NSIF schedule balanced","al3d":"42 lines tie to ledger.",
"open_sched":"Open schedules","bank_file":"Bank file","recent_title":"Recent runs","cal_title":"Calendar",
"th_period":"Period","th_scope":"Scope","th_gross":"Gross SDG","th_nsif":"NSIF 25%","th_pit":"PIT","th_net":"Net SDG","th_status":"Status",
"st_pending":"Awaiting approval","st_posted":"Posted","st_done":"Done","st_sched":"Scheduled","st_queue":"Queued","st_locked":"Locked",
"tot2":"2 runs","cal1":"FX lock + CSV","cal2":"Approval","cal3":"Bank file","cal4":"NSIF/PIT filing",
"emp_eb":"Directory · EMPFILE.cpy","emp_title":"Employees","emp_lede":"ID, national ID, hire date, base currency, COMP-3 salary, NSIF flag, bank.",
"th_emp":"Employee","th_hire":"Hire","th_base":"Base","th_sal":"Base salary","th_allow":"Allowances","th_nsifc":"NSIF","th_bank":"Bank",
"run_eb":"PRL-CALC · FX-NORM · TAX-SUD · NSIF-ENG","run_title":"Payroll Run",
"rs1t":"01 · LOCK FX","rs1d":"USD 2610.50 · SAR 696.10 · AED 710.85 · 25 Sep 09:00","rs2t":"02 · IMPORT","rs2d":"42 rows · 0 errors · 3 warnings","rs3t":"03 · COMPUTE","rs3d":"libpayroll.so COMP-3 rounding","rs4t":"04 · APPROVE + POST","rs4d":"Approval → Bankak file",
"batch_title":"Batch result · 2026-09 · 42 employees","th_cur":"Currency","th_gross2":"Gross SDG","th_e8":"NSIF emp 8%","th_c17":"NSIF co 17%","th_tax":"Taxable","tot42":"Totals · 42 lines",
"pay_eb":"Delivery · WhatsApp / Telegram","pay_title":"Payslips","slip_title":"SD-0042 · Amal O. Hassan · Sep 2026","log_title":"Delivery log","text7":"Text 7 KB",
"dl1":"Delivered 09:41","dl2":"Read 09:44","dl3":"Retrying","dl4":"Queued",
"fx_eb":"FX-NORM · to SDG","fx_title":"FX Rates","trend_title":"September trend","trend_note":"Locked rate stamps every run (S9(5)V94) for replay.","rate_title":"Rate table","th_date":"Date","th_src":"Source",
"rep_eb":"NSIF / PIT / Zakat / ESG","rep_title":"Reports","nsif_title":"NSIF schedule · 25%","pit_title":"PIT schedule · exempt 50,000","esg_title":"Gratuity accrual · ESG-VAL","esg_note":"<3yr ⅓× · 3–5yr ½× · 5–10yr 1× · >10yr 1.5×","file_title":"Filing checklist","bal_t":"Tax file balanced","bal_d":"Taxable = Gross − NSIF-Emp","nis_t":"2 staff above nisab","nis_d":"Zakat after PIT, consent required.","th_br":"Bracket","tot42l":"42 lines",
"bank_eb":"Bankak / Faisal / Omdurman","bank_title":"Bank Export","file2_title":"Direct-debit file · 42 lines · fixed-width","th_acct":"Account","th_bank2":"Bank","th_net2":"Net SDG","th_ref":"Ref","th_st":"Status","valid":"Valid","sftp":"Copy SFTP path",
"ten_eb":"Multi-tenant operations","ten_title":"Tenants & Users","cli_title":"Clients","roles_title":"Roles","r_owner":"Owner — approve + post + export","r_acct":"Accountant — run + FX draft","r_view":"Viewer — payslips only","roles_note":"Sessions in SQLite; payroll math isolated from web roles.","th_client":"Client","th_plan":"Plan","th_empn":"Emp",
"aud_eb":"Replayable history","aud_title":"Audit Log","th_time":"Time","th_actor":"Actor","th_action":"Action","th_hash":"Hash","aud_note":"Each run stores FX + table version for recompile-free replay.","ac1":"FX locked USD 2610.50","ac2":"Run 2026-09 · 42 rows · 11ms","ac3":"Payslip SD-0042 sent",
"set_eb":"Versioned data files · no recompile","set_title":"Statutory Tables","rates_title":"Rates v2026.09","f_e":"NSIF employee","f_c":"NSIF employer","f_free":"Tax-free SDG","f_t2":"Tier 2 low","f_t3":"Tier 3 medium","f_t45":"Tier 4/5 high/top","pub":"Publish v2026.10 draft","roll":"Rollback v2026.08","set_note":"Tables are data — binaries stay stable for years.",
"wl_gross":"Gross","wl_nsif":"NSIF employee −8%","wl_tax":"Taxable base","wl_pit":"PIT over 50k exempt","wl_net":"Net pay SDG"
},
ar:{
"nav_operate":"التشغيل","nav_compliance":"الامتثال","nav_admin":"الإدارة","nav_dashboard":"لوحة التحكم","nav_employees":"الموظفون","nav_run":"مسير الرواتب","nav_payslips":"قسائم الراتب","nav_fx":"أسعار الصرف","nav_reports":"التقارير","nav_bank":"ملف البنك","nav_tenants":"العملاء والمستخدمون","nav_audit":"سجل التدقيق","nav_settings":"الجداول القانونية",
"top_period":"الفترة","top_new":"مسير جديد","top_site":"الموقع","search_ph":"ابحث بالاسم أو الرقم الوطني أو البنك…","btn_import":"استيراد CSV","btn_add":"إضافة موظف","btn_approve":"اعتماد","btn_export":"تصدير","btn_download":"تنزيل الملف","btn_send":"إرسال",
"ov_eb":"النيل الزراعية · سبتمبر 2026","ov_title":"نظرة عامة على الرواتب","ov_lede":"حالة الفترة والأرصدة والبنود المعلقة. هذه اللوحة للتشغيل فقط.",
"kpi_head":"عدد الموظفين","kpi_head_s":"3 عملات · 3 تنبيهات تأمينات","kpi_gross":"الإجمالي بالجنيه","kpi_gross_s":"الصرف مثبت 25 سبتمبر 09:00","kpi_nsif":"التأمينات 25%","kpi_nsif_s":"موظف 8% + صاحب عمل 17%","kpi_net":"الصافي بالجنيه","kpi_net_s":"بانتظار الاعتماد",
"trace_title":"تتبع الحساب · موظف واحد","pend_title":"بنود معلقة",
"al1t":"3 عقود بدون علم التأمينات","al1d":"راجع قبل الترحيل.","al2t":"تغيّر نصاب الزكاة","al2d":"أعد التحقق لموظفين.","al3t":"جدول التأمينات متوازن","al3d":"42 سطراً تطابق الأستاذ.",
"open_sched":"فتح الجداول","bank_file":"ملف البنك","recent_title":"المسيرات الأخيرة","cal_title":"التقويم",
"th_period":"الفترة","th_scope":"النطاق","th_gross":"الإجمالي جنيه","th_nsif":"التأمينات 25%","th_pit":"الضريبة","th_net":"الصافي جنيه","th_status":"الحالة",
"st_pending":"بانتظار الاعتماد","st_posted":"مرحّل","st_done":"تم","st_sched":"مجدول","st_queue":"في الانتظار","st_locked":"مثبت",
"tot2":"مسيران","cal1":"تثبيت الصرف + CSV","cal2":"الاعتماد","cal3":"ملف البنك","cal4":"توريد التأمينات والضريبة",
"emp_eb":"الدليل · EMPFILE.cpy","emp_title":"الموظفون","emp_lede":"الرقم والرقم الوطني وتاريخ التعيين والعملة الأساسية والراتب COMP-3 وعلم التأمينات والبنك.",
"th_emp":"الموظف","th_hire":"التعيين","th_base":"العملة","th_sal":"الراتب الأساسي","th_allow":"البدلات","th_nsifc":"التأمينات","th_bank":"البنك",
"run_eb":"الأجور · توحيد الصرف · الضريبة · التأمينات","run_title":"مسير الرواتب",
"rs1t":"01 · تثبيت الصرف","rs1d":"دولار 2610.50 · ريال 696.10 · درهم 710.85 · 25 سبتمبر","rs2t":"02 · الاستيراد","rs2d":"42 صفاً · 0 أخطاء · 3 تنبيهات","rs3t":"03 · الحساب","rs3d":"تقريب COMP-3 عبر libpayroll.so","rs4t":"04 · الاعتماد والترحيل","rs4d":"الاعتماد ← ملف بنكك",
"batch_title":"نتيجة الدفعة · سبتمبر 2026 · 42 موظفاً","th_cur":"العملة","th_gross2":"الإجمالي جنيه","th_e8":"تأمينات الموظف 8%","th_c17":"تأمينات صاحب العمل 17%","th_tax":"الوعاء","tot42":"الإجمالي · 42 سطراً",
"pay_eb":"التسليم · واتساب / تيليجرام","pay_title":"قسائم الراتب","slip_title":"SD-0042 · أمل حسن · سبتمبر 2026","log_title":"سجل التسليم","text7":"نسخة نصية 7 ك.ب",
"dl1":"تم التسليم 09:41","dl2":"تمت القراءة 09:44","dl3":"جارٍ إعادة المحاولة","dl4":"في الانتظار",
"fx_eb":"توحيد الصرف · مقابل الجنيه","fx_title":"أسعار الصرف","trend_title":"اتجاه سبتمبر","trend_note":"السعر المثبت يُختم على كل مسير (S9(5)V94) لإعادة التدقيق.","rate_title":"جدول الأسعار","th_date":"التاريخ","th_src":"المصدر",
"rep_eb":"التأمينات / الضريبة / الزكاة / المكافأة","rep_title":"التقارير","nsif_title":"جدول التأمينات · 25%","pit_title":"جدول الضريبة · إعفاء 50,000","esg_title":"مكافأة نهاية الخدمة","esg_note":"أقل من 3 سنوات ⅓× · 3–5 نصف × · 5–10 شهر × · أكثر من 10 شهر ونصف","file_title":"قائمة التقديم","bal_t":"ملف الضريبة متوازن","bal_d":"الوعاء = الإجمالي − حصة الموظف","nis_t":"موظفان فوق النصاب","nis_d":"الزكاة بعد الضريبة وتتطلب موافقة.","th_br":"الشريحة","tot42l":"42 سطراً",
"bank_eb":"بنكك / فيصل / أم درمان","bank_title":"ملف البنك","file2_title":"ملف الخصم المباشر · 42 سطراً · ثابت العرض","th_acct":"الحساب","th_bank2":"البنك","th_net2":"الصافي جنيه","th_ref":"المرجع","th_st":"الحالة","valid":"صالح","sftp":"نسخ مسار SFTP",
"ten_eb":"تشغيل متعدد العملاء","ten_title":"العملاء والمستخدمون","cli_title":"العملاء","roles_title":"الأدوار","r_owner":"المالك — اعتماد + ترحيل + تصدير","r_acct":"المحاسب — تشغيل + مسودة الصرف","r_view":"مشاهد — القسائم فقط","roles_note":"الجلسات في SQLite والحسابات معزولة عن أدوار الويب.","th_client":"العميل","th_plan":"الباقة","th_empn":"الموظفون",
"aud_eb":"سجل قابل لإعادة التشغيل","aud_title":"سجل التدقيق","th_time":"الوقت","th_actor":"الفاعل","th_action":"الإجراء","th_hash":"البصمة","aud_note":"كل مسير يخزن الصرف ونسخة الجداول لإعادة التشغيل بدون تجميع.","ac1":"تثبيت الدولار 2610.50","ac2":"مسير سبتمبر · 42 صفاً · 11 مللي ثانية","ac3":"إرسال قسيمة SD-0042",
"set_eb":"ملفات بيانات مُصدَرة · بدون تجميع","set_title":"الجداول القانونية","rates_title":"النسب v2026.09","f_e":"تأمينات الموظف","f_c":"تأمينات صاحب العمل","f_free":"الإعفاء بالجنيه","f_t2":"الشريحة الدنيا","f_t3":"الشريحة الوسطى","f_t45":"العليا / القصوى","pub":"نشر مسودة v2026.10","roll":"الرجوع لـ v2026.08","set_note":"الجداول بيانات — البرنامج يبقى ثابتاً لسنوات.",
"wl_gross":"الإجمالي","wl_nsif":"تأمينات الموظف −8%","wl_tax":"الوعاء الضريبي","wl_pit":"الضريبة فوق إعفاء 50 ألف","wl_net":"الصافي بالجنيه"
}};
(function(){
  const root=document.documentElement;
  function get(){const s=localStorage.getItem('smcpe-lang');if(s)return s;try{if((navigator.language||'').toLowerCase().startsWith('ar'))return 'ar';}catch(e){}return 'ar';}
  function apply(l){
    const d=SMCPE_DASH_I18N[l]||SMCPE_DASH_I18N.en;
    document.querySelectorAll('[data-i18n]').forEach(el=>{const k=el.getAttribute('data-i18n');if(d[k]!=null)el.textContent=d[k];});
    document.querySelectorAll('[data-i18n-ph]').forEach(el=>{const k=el.getAttribute('data-i18n-ph');if(d[k]!=null)el.setAttribute('placeholder',d[k]);});
    root.lang=l;root.dir=(l==='ar')?'rtl':'ltr';
    try{localStorage.setItem('smcpe-lang',l);}catch(e){}
    const t=document.getElementById('dashLangToggle');if(t)t.textContent=(l==='ar')?'EN':'عربي';
    if(window.SMCPE_rerenderWater)window.SMCPE_rerenderWater();
  }
  window.SMCPE_dashLang={get,apply};
  document.addEventListener('DOMContentLoaded',()=>{apply(get());
    const t=document.getElementById('dashLangToggle');
    if(t)t.addEventListener('click',()=>apply(get()==='ar'?'en':'ar'));});
})();
