-- Seed data for notifications-related scenarios

-- Low stock product
INSERT OR REPLACE INTO products(id,name,current_stock,minimum_stock,active)
VALUES(1001,'منتج منخفض',2,5,1);

-- Pending invoice due in 3 days
INSERT OR REPLACE INTO invoices(id,invoice_number,customer_name,total_amount,status,due_date)
VALUES(2001,'INV-2001','عميل تجريبي',1500.00,'pending',date('now','+3 day'));

-- Active reminder due now
INSERT OR REPLACE INTO reminders(id,title,description,reminder_time,status)
VALUES(3001,'متابعة','اتصل بالعميل',datetime('now'),'active');
