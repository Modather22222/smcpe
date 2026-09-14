      * STATUTORY.cpy — versioned statutory tables, no recompile needed
      * Loaded per run via statutory_version (e.g. v2026.09)
       01  STATUTORY-TABLE.
           05  ST-VERSION              PIC X(08).  *> v2026.09
           05  ST-NSIF-EMP-RATE        PIC 9V99 VALUE 0.08.
           05  ST-NSIF-CO-RATE         PIC 9V99 VALUE 0.17.
           05  ST-TAX-FREE-LIMIT       PIC 9(7)V99 VALUE 50000.00.
           05  ST-TAX-TIERS OCCURS 4 TIMES.
               10  ST-TIER-LIMIT       PIC 9(9)V99.
               10  ST-TIER-RATE        PIC 9V99.
      * Tier meaning (progressive):
      *   1: exempt 0-50k (rate 0, handled via FREE-LIMIT)
      *   2: 50k-100k 5%
      *   3: 100k-200k 10%
      *   4: 200k-400k 15%
      *   5: >400k 20% (overflow tier 4 rate 0.20)
