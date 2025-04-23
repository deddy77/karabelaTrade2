# Test lot size rounding
test_lot = 0.042535
print(f"Original lot size: {test_lot}")

# First round in open_buy_order/open_sell_order
lot = round(float(test_lot), 2)
print(f"After first rounding: {lot}")

# Second round in prepare_order_request
final_lot = round(float(lot), 2)
print(f"After second rounding: {final_lot}")

print("\nConclusion: A lot size of 0.042535 would be rounded to 0.04")
