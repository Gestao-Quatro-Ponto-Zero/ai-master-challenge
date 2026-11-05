insert into public.products (product, series, sales_price) values
('GTX Basic', 'GTX', 550),
('GTX Pro', 'GTX', 4821),
('MG Special', 'MG', 55),
('MG Advanced', 'MG', 3393),
('GTX Plus Pro', 'GTX', 5482),
('GTX Plus Basic', 'GTX', 1096),
('GTK 500', 'GTK', 26768)
on conflict do nothing;
