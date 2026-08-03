const { createSlice, configureStore } = ReduxToolkit;

// Load cart state from LocalStorage to persist data on page refresh
const loadCartState = () => {
  try {
    const serializedState = localStorage.getItem("beman_global_cart");
    return serializedState ? JSON.parse(serializedState) : { items: [] };
  } catch (err) {
    return { items: [] };
  }
};

const initialState = loadCartState();

// Create Cart Slice and define reducer actions
const cartSlice = createSlice({
  name: "cart",
  initialState,
  reducers: {
    addItem: (state, action) => {
      const { id, name, price, image, maxStock, quantity } = action.payload;
      const existingItem = state.items.find((item) => item.id === id);

      if (existingItem) {
        if (existingItem.quantity + quantity <= maxStock) {
          existingItem.quantity += quantity;
        } else {
          alert(`Sorry, only ${maxStock} units available in stock.`);
          existingItem.quantity = maxStock;
        }
      } else {
        state.items.push({ id, name, price, image, maxStock, quantity });
      }

      // Write updated state to LocalStorage
      localStorage.setItem("beman_global_cart", JSON.stringify(state));
    },
    removeItem: (state, action) => {
      state.items = state.items.filter((item) => item.id !== action.payload);
      localStorage.setItem("beman_global_cart", JSON.stringify(state));
    },
  },
});

// Extract actions from the slice
const { addItem, removeItem } = cartSlice.actions;

// Configure the global Redux Store
const store = configureStore({
  reducer: {
    cart: cartSlice.reducer,
  },
});

// Expose store and actions to the window object for global application access
window.cartStore = store;
window.addCartItemAction = addItem;
window.removeCartItemAction = removeItem;
