       01  PAYROLL-CALC-RECORD.
           05  PRL-EMP-ID              PIC X(10).
           05  PRL-PERIOD-DATE         PIC X(06).  *> YYYYMM
           05  PRL-EXCHANGE-RATE       PIC S9(5)V9(4) COMP-3. *> Base FX to SDG S9(5)V9(4)
           05  PRL-GROSS-SDG           PIC S9(11)V99 COMP-3.
           05  PRL-NSIF-EMPLOYEE-SDG   PIC S9(9)V99 COMP-3.  *> 8% Employee
           05  PRL-NSIF-EMPLOYER-SDG   PIC S9(9)V99 COMP-3.  *> 17% Employer
           05  PRL-TAXABLE-INCOME-SDG  PIC S9(11)V99 COMP-3.
           05  PRL-PIT-TAX-SDG         PIC S9(9)V99 COMP-3.  *> Personal Income Tax
           05  PRL-ZAKAT-DEDUCTION-SDG PIC S9(9)V99 COMP-3.
           05  PRL-NET-PAY-SDG         PIC S9(11)V99 COMP-3.
           05  PRL-NET-PAY-FX          PIC S9(9)V99 COMP-3.
