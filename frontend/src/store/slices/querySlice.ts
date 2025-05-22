import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface QueryState {
  history: string[];
  favorites: string[];
  results: any[];
  loading: boolean;
  error: string | null;
}

const initialState: QueryState = {
  history: [],
  favorites: [],
  results: [],
  loading: false,
  error: null
};

export const querySlice = createSlice({
  name: 'query',
  initialState,
  reducers: {
    setResults: (state, action) => {
      state.results = action.payload;
    },
    addToHistory: (state, action) => {
      state.history.unshift(action.payload);
    },
    toggleFavorite: (state, action) => {
      // Toggle favorite query logic
    }
  }
});