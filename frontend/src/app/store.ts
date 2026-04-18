import { configureStore, createSlice, PayloadAction } from "@reduxjs/toolkit";

type AuthState = {
  accessToken: string | null;
  user: { id: string; email: string; role: string } | null;
};

const authSlice = createSlice({
  name: "auth",
  initialState: {
    accessToken: localStorage.getItem("access_token"),
    user: localStorage.getItem("user") ? JSON.parse(localStorage.getItem("user") as string) : null,
  } as AuthState,
  reducers: {
    setAuth(state, action: PayloadAction<AuthState>) {
      state.accessToken = action.payload.accessToken;
      state.user = action.payload.user;
      if (action.payload.accessToken) {
        localStorage.setItem("access_token", action.payload.accessToken);
      }
      if (action.payload.user) {
        localStorage.setItem("user", JSON.stringify(action.payload.user));
      }
    },
    logout(state) {
      state.accessToken = null;
      state.user = null;
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
    },
  },
});

type SessionState = {
  sessionId: string | null;
  uploaded: boolean;
  located: boolean;
  images: { file: File; role: string }[];
  shopTypeDetection: {
    shopType: string;
    confidence: number;
    source: string;
    reasoning: string[];
    topCandidates: { shopType: string; confidence: number; reasons: string[] }[];
    needsConfirmation: boolean;
  } | null;
  optionalVideo: { fileName: string; durationSeconds: number } | null;
  optionalInputs: {
    shopType: string;
    shopSizeSqft: string;
    monthlyRent: string;
    yearsInOperation: string;
    shopTypeConfirmedByUser: boolean;
  };
  location: { lat: number; lng: number; formatted_address?: string } | null;
};

const sessionSlice = createSlice({
  name: "session",
  initialState: {
    sessionId: null,
    uploaded: false,
    located: false,
    images: [],
    shopTypeDetection: null,
    optionalVideo: null,
    optionalInputs: {
      shopType: "kirana_general",
      shopSizeSqft: "180",
      monthlyRent: "15000",
      yearsInOperation: "6",
      shopTypeConfirmedByUser: true,
    },
    location: null,
  } as SessionState,
  reducers: {
    setSessionId(state, action: PayloadAction<string>) {
      state.sessionId = action.payload;
    },
    setImages(state, action: PayloadAction<{ file: File; role: string }[]>) {
      state.images = action.payload;
    },
    setShopTypeDetection(state, action: PayloadAction<SessionState["shopTypeDetection"]>) {
      state.shopTypeDetection = action.payload;
      if (action.payload?.shopType) {
        state.optionalInputs.shopType = action.payload.shopType;
        state.optionalInputs.shopTypeConfirmedByUser = !action.payload.needsConfirmation;
      }
    },
    setOptionalVideo(state, action: PayloadAction<SessionState["optionalVideo"]>) {
      state.optionalVideo = action.payload;
    },
    setOptionalInputs(state, action: PayloadAction<Partial<SessionState["optionalInputs"]>>) {
      state.optionalInputs = { ...state.optionalInputs, ...action.payload };
    },
    markUploaded(state, action: PayloadAction<boolean>) {
      state.uploaded = action.payload;
    },
    setLocation(state, action: PayloadAction<SessionState["location"]>) {
      state.location = action.payload;
      state.located = Boolean(action.payload);
    },
  },
});

const predictionSlice = createSlice({
  name: "prediction",
  initialState: { predictionId: null as string | null, result: null as any | null },
  reducers: {
    setPredictionId(state, action: PayloadAction<string>) {
      state.predictionId = action.payload;
    },
    setPredictionResult(state, action: PayloadAction<any>) {
      state.result = action.payload;
    },
  },
});

const simulationSlice = createSlice({
  name: "simulation",
  initialState: { result: null as any | null },
  reducers: {
    setSimulationResult(state, action: PayloadAction<any>) {
      state.result = action.payload;
    },
  },
});

export const { setAuth, logout } = authSlice.actions;
export const { setSessionId, setImages, setShopTypeDetection, setOptionalVideo, setOptionalInputs, markUploaded, setLocation } = sessionSlice.actions;
export const { setPredictionId, setPredictionResult } = predictionSlice.actions;
export const { setSimulationResult } = simulationSlice.actions;

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    session: sessionSlice.reducer,
    prediction: predictionSlice.reducer,
    simulation: simulationSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
