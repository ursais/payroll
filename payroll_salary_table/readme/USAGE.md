Salary Tables are maintained at Payroll / Configuration / Salary Tables.

On a Salary Table record you can set:

- Template: the salary tenplate being used
- Company : the company it applies to (all if left enpty)
- Start and End Dates: the validity period (optional)
- Note: allows to add notes
- Lines: enter each combination and the Result value to be used when matched

Salary tables can be used on a salary rule with the follwoing expression:
```
value = contract.salary_table("CODE")
```
