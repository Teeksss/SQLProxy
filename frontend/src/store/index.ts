import { configureStore } from '@reduxjs/toolkit';
import queryReducer from './slices/querySlice';
import serverReducer from './slices/serverSlice';
import analyticsReducer from './slices/analyticsSlice';
import settingsReducer from './slices/settingsSlice';

export const store = configureStore({
  reducer: {
    query: queryReducer,
    server: serverReducer,
    analytics: analyticsReducer,
    settings: settingsReducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false
    })
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;