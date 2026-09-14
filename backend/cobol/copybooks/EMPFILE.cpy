       01  EMPLOYEE-RECORD.
           05  EMP-ID                  PIC X(10).
           05  EMP-NAME                PIC X(40).
           05  EMP-NATIONAL-ID         PIC X(15).
           05  EMP-HIRE-DATE.
               10  EMP-HIRE-YEAR       PIC 9(04).
               10  EMP-HIRE-MONTH      PIC 9(02).
               10  EMP-HIRE-DAY        PIC 9(02).
           05  EMP-BASE-CURRENCY       PIC X(03).  *> SDG, USD, SAR, AED
           05  EMP-BASE-SALARY         PIC S9(9)V99 COMP-3.
           05  EMP-ALLOWANCES-SDG      PIC S9(9)V99 COMP-3.
           05  EMP-ALLOWANCES-FX       PIC S9(9)V99 COMP-3.
           05  EMP-NSIF-ELIGIBLE       PIC X(01).  *> 'Y' or 'N'
           05  EMP-MARITAL-STATUS      PIC X(01).  *> 'S'=Single, 'M'=Married
           05  EMP-BANK-ACCOUNT        PIC X(24).
           05  EMP-BANK-CODE           PIC X(08).
