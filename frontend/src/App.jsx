// import { useEffect, useMemo, useRef, useState } from 'react'

// const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
// const TOKEN_KEY = 'vitamin_ai_token'
// const USER_KEY = 'vitamin_ai_username'

// const initialQuestionnaire = {
//   fatigue: 1,
//   diet_type: 'omnivore',
//   vegetarian: 0,
//   pregnancy: 0,
//   sunlight_exposure: 2,
//   medications: 0,
//   chronic_illness: 0,
//   allergies: 0,
//   lactose_intolerance: 0
// }

// const quickPrompts = [
//   'What does my severity mean?',
//   'Give me a practical food plan for today',
//   'When should I consult a specialist?'
// ]

// function toPercent(value) {
//   return `${Math.round((value || 0) * 100)}%`
// }

// // function AnalysisResult({ bundle, title }) {
// //   if (!bundle) {
// //     return (
// //       <article className="card result-empty">
// //         <h3>{title}</h3>
// //         <p>Run an analysis to view prediction, severity alerts, food recommendations, and heatmaps.</p>
// //       </article>
// //     )
// //   }

// //   const prediction = bundle.prediction || {}
// //   // =========================================================================
// //   // Fix - handling severity displays (14-03-2026)

// //   const severity = prediction.severity || 0;
// //   const threshold = prediction.severity_threshold || 0.72;

// //   let statusLabel = "OK";
// //   let statusClass = "status-ok"; // Green

// //   if (severity >= threshold) {
// //     statusLabel = "Severe";
// //     statusClass = "status-alert"; // Red
// //   } else if (severity >= threshold - 0.15) { 
// //     // If severity is within 0.15 of the threshold, mark as Mild
// //     statusLabel = "Mild";
// //     statusClass = "status-warning"; // Yellow (we will add this class)
// //   }

// //   // Fix - ended here
// //   // ===================================================================================
  
// //   const result = bundle.result || {}
// //   const diet = bundle.diet || {}
// //   const probabilities = Object.entries(prediction.probabilities || {}).sort((a, b) => b[1] - a[1])
// //   const rankedFoods = (diet.ranked_foods || []).slice(0, 10)
// //   const mealPlan = Object.entries(diet.meal_plan || {})
// //   const heatmaps = result.heatmaps || []

// //   return (
// //     <div className="result-stack">

// //       {/* =========================================================================================== */}
// //       {/* Fix - Severity handling */}

// //       {statusLabel === "Severe" && (
// //         <div className="critical-alert-banner">
// //           <div className="alert-content">
// //             <h2>⚠️ CRITICAL SEVERITY DETECTED</h2>
// //             <p>Your analysis indicates a high probability of severe vitamin deficiency. Please prioritize professional medical consultation immediately.</p>
// //           </div>
// //         </div>
// //       )}

// //       {/* Fix ends here */}
// //       {/* =========================================================================================== */}
      
// //       <article className="card">
// //         <div className="card-head">
// //           <h3>{title}</h3>
          
// //           {/* ================================================================================== */}
// //           {/* Fix - handling severity displays (14-03-2026)  */}
// //           <span className={`status-pill ${statusClass}`}>
// //             {statusLabel}
// //           {/* <span className={`status-pill ${prediction.severity_alert ? 'status-alert' : 'status-ok'}`}>
// //             {prediction.severity_alert ? 'Alert triggered' : 'Within threshold'} */}
// //             {/* Fix ended here */}
// //             {/* ================================================================================ */}
            
// //           </span>
// //         </div>
// //         <p className="muted">Updated: {new Date(bundle.createdAt).toLocaleString()}</p>
// //         <div className="metrics-grid">
// //           <div className="metric-block">
// //             <label>Predicted class</label>
// //             <strong>{prediction.predicted_class || 'n/a'}</strong>
// //           </div>
// //           <div className="metric-block">
// //             <label>Confidence</label>
// //             <strong>{toPercent(prediction.confidence)}</strong>
// //           </div>
// //           <div className="metric-block">
// //             <label>Severity</label>
// //             <strong>{toPercent(prediction.severity)}</strong>
// //           </div>
// //           <div className="metric-block">
// //             <label>Threshold</label>
// //             <strong>{toPercent(prediction.severity_threshold)}</strong>
// //           </div>
// //         </div>
// //         <div className="gauge-shell">
// //           <div className="gauge-fill" style={{ width: toPercent(prediction.severity) }} />
// //           <span>Severity {toPercent(prediction.severity)}</span>
// //         </div>
// //       </article>

// //       {/* 1. Only show breakdown/foods if NOT "OK" */}
// //       {statusLabel !== "OK" ? (
// //         <>
// //         <article className="card">
// //           <h3>Probability Breakdown</h3>
// //           <ul className="compact-list">
// //             {probabilities.map(([label, value]) => (
// //               <li key={label}>
// //                 <span>{label}</span>
// //                 <strong>{toPercent(value)}</strong>
// //               </li>
// //             ))}
// //           </ul>
// //         </article>

// //       <article className="card">
// //         <h3>Top Recommended Foods</h3>
// //         {rankedFoods.length === 0 ? (
// //           <p className="muted">Diet recommendation not available.</p>
// //         ) : (
// //           <ul className="compact-list">
// //             {rankedFoods.map((item) => (
// //               <li key={`${item.food_name}-${item.source_dataset}`}>
// //                 <span>{item.food_name}</span>
// //                 <strong>{item.score?.toFixed(3)}</strong>
// //               </li>
// //             ))}
// //           </ul>
// //         )}
// //       </article>

// //       <article className="card">
// //         <h3>Meal Plan</h3>
// //         {mealPlan.length === 0 ? (
// //           <p className="muted">Meal plan unavailable.</p>
// //         ) : (
// //           <ul className="compact-list">
// //             {mealPlan.map(([slot, item]) => (
// //               <li key={slot}>
// //                 <span>{slot}</span>
// //                 <strong>{item?.food_name || 'n/a'}</strong>
// //               </li>
// //             ))}
// //           </ul>
// //         )}
// //         {diet.medical_advice ? (
// //           <p className={`advice ${diet.consult_specialist ? 'advice-alert' : 'advice-ok'}`}>{diet.medical_advice}</p>
// //         ) : null}
// //       </article>

// //       {/* =============================================================================== */}
// //       {/* Fix - Message shown if status is ok */}

// //           {/* Message shown when status is OK */}
// //           <article className="card status-ok-message">
// //             <h3>Results: Healthy</h3>
// //             <p>Your indicators are within normal ranges. No specific dietary changes are recommended at this time. Maintain your current healthy lifestyle!</p>
// //           </article>
// //         )}

// //       {/* Fix ends here */}
// //       {/* ==================================================================================== */}

// //       <article className="card heatmap-card">
// //         <h3>Grad-CAM Viewer</h3>
// //         {heatmaps.length === 0 ? (
// //           <p className="muted">No heatmaps generated for this run.</p>
// //         ) : (
// //           <div className="heatmap-grid">
// //             {heatmaps.map((hm) => (
// //               <div className="heatmap-pair" key={hm.image_id}>
// //                 <figure>
// //                   <img src={`data:image/jpeg;base64,${hm.base_b64}`} alt="Base frame" />
// //                   <figcaption>Base</figcaption>
// //                 </figure>
// //                 <figure>
// //                   <img src={`data:image/jpeg;base64,${hm.overlay_b64}`} alt="Grad-CAM overlay" />
// //                   <figcaption>Grad-CAM</figcaption>
// //                 </figure>
// //               </div>
// //             ))}
// //           </div>
// //         )}
// //       </article>
// //     </div>
// //   )
// // }

// function AnalysisResult({ bundle, title }) {
//   if (!bundle) {
//     return (
//       <article className="card result-empty">
//         <h3>{title}</h3>
//         <p>
//           Run an analysis to view prediction, severity alerts, food
//           recommendations, and heatmaps.
//         </p>
//       </article>
//     )
//   }

//   const prediction = bundle.prediction || {}

//   const severity = prediction.severity || 0
//   const threshold = prediction.severity_threshold || 0.72

//   let statusLabel = "OK"
//   let statusClass = "status-ok"

//   if (severity >= threshold) {
//     statusLabel = "Severe"
//     statusClass = "status-alert"
//   } else if (severity >= threshold - 0.15) {
//     statusLabel = "Mild"
//     statusClass = "status-warning"
//   }

//   const result = bundle.result || {}
//   const diet = bundle.diet || {}

//   const probabilities = Object.entries(prediction.probabilities || {}).sort(
//     (a, b) => b[1] - a[1]
//   )

//   const rankedFoods = (diet.ranked_foods || []).slice(0, 10)

//   const mealPlan = Object.entries(diet.meal_plan || {})

//   const heatmaps = result.heatmaps || []

//   return (
//     <div className="result-stack">

//       {statusLabel === "Severe" && (
//         <div className="critical-alert-banner">
//           <div className="alert-content">
//             <h2>⚠️ CRITICAL SEVERITY DETECTED</h2>
//             <p>
//               Your analysis indicates a high probability of severe vitamin
//               deficiency. Please consult a medical professional immediately.
//             </p>
//           </div>
//         </div>
//       )}

//       <article className="card">
//         <div className="card-head">
//           <h3>{title}</h3>
//           <span className={`status-pill ${statusClass}`}>
//             {statusLabel}
//           </span>
//         </div>

//         <p className="muted">
//           Updated: {new Date(bundle.createdAt).toLocaleString()}
//         </p>

//         <div className="metrics-grid">
//           <div className="metric-block">
//             <label>Predicted class</label>
//             <strong>{prediction.predicted_class || "n/a"}</strong>
//           </div>

//           <div className="metric-block">
//             <label>Confidence</label>
//             <strong>{toPercent(prediction.confidence)}</strong>
//           </div>

//           <div className="metric-block">
//             <label>Severity</label>
//             <strong>{toPercent(prediction.severity)}</strong>
//           </div>

//           <div className="metric-block">
//             <label>Threshold</label>
//             <strong>{toPercent(prediction.severity_threshold)}</strong>
//           </div>
//         </div>

//         <div className="gauge-shell">
//           <div
//             className="gauge-fill"
//             style={{ width: toPercent(prediction.severity) }}
//           />
//           <span>Severity {toPercent(prediction.severity)}</span>
//         </div>
//       </article>

//       {statusLabel !== "OK" ? (
//         <>
//           <article className="card">
//             <h3>Probability Breakdown</h3>
//             <ul className="compact-list">
//               {probabilities.map(([label, value]) => (
//                 <li key={label}>
//                   <span>{label}</span>
//                   <strong>{toPercent(value)}</strong>
//                 </li>
//               ))}
//             </ul>
//           </article>

//           <article className="card">
//             <h3>Top Recommended Foods</h3>

//             {rankedFoods.length === 0 ? (
//               <p className="muted">Diet recommendation not available.</p>
//             ) : (
//               <ul className="compact-list">
//                 {rankedFoods.map((item) => (
//                   <li key={`${item.food_name}-${item.source_dataset}`}>
//                     <span>{item.food_name}</span>
//                     <strong>{item.score?.toFixed(3)}</strong>
//                   </li>
//                 ))}
//               </ul>
//             )}
//           </article>

//           <article className="card">
//             <h3>Meal Plan</h3>

//             {mealPlan.length === 0 ? (
//               <p className="muted">Meal plan unavailable.</p>
//             ) : (
//               <ul className="compact-list">
//                 {mealPlan.map(([slot, item]) => (
//                   <li key={slot}>
//                     <span>{slot}</span>
//                     <strong>{item?.food_name || "n/a"}</strong>
//                   </li>
//                 ))}
//               </ul>
//             )}

//             {diet.medical_advice && (
//               <p
//                 className={`advice ${
//                   diet.consult_specialist ? "advice-alert" : "advice-ok"
//                 }`}
//               >
//                 {diet.medical_advice}
//               </p>
//             )}
//           </article>
//         </>
//       ) : (
//         <article className="card status-ok-message">
//           <h3>Results: Healthy</h3>
//           <p>
//             Your indicators are within normal ranges. No specific dietary
//             changes are recommended at this time. Maintain your current
//             healthy lifestyle.
//           </p>
//         </article>
//       )}

//       <article className="card heatmap-card">
//         <h3>Grad-CAM Viewer</h3>

//         {heatmaps.length === 0 ? (
//           <p className="muted">No heatmaps generated for this run.</p>
//         ) : (
//           <div className="heatmap-grid">
//             {heatmaps.map((hm) => (
//               <div className="heatmap-pair" key={hm.image_id}>
//                 <figure>
//                   <img
//                     src={`data:image/jpeg;base64,${hm.base_b64}`}
//                     alt="Base frame"
//                   />
//                   <figcaption>Base</figcaption>
//                 </figure>

//                 <figure>
//                   <img
//                     src={`data:image/jpeg;base64,${hm.overlay_b64}`}
//                     alt="Grad-CAM overlay"
//                   />
//                   <figcaption>Grad-CAM</figcaption>
//                 </figure>
//               </div>
//             ))}
//           </div>
//         )}
//       </article>

//     </div>
//   )
// }

// function LoginView({
//   authMode,
//   setAuthMode,
//   loginForm,
//   setLoginForm,
//   signupForm,
//   setSignupForm,
//   loginLoading,
//   signupLoading,
//   loginError,
//   signupError,
//   onLogin,
//   onSignup
// }) {
//   const activeError = authMode === 'login' ? loginError : signupError
//   const activeLoading = authMode === 'login' ? loginLoading : signupLoading
//   const activeSubmit = authMode === 'login' ? onLogin : onSignup

//   return (
//     <div className="login-shell">
//       <div className="aura aura-one" />
//       <div className="aura aura-two" />
//       <form className="login-card" onSubmit={activeSubmit}>
//         <h1>Vitamin AI Clinical Console</h1>
//         <p>
//           Secure access for image + questionnaire analysis, live camera triage, and AI-guided nutrition planning.
//         </p>

//         <div className="auth-switch">
//           <button
//             type="button"
//             className={authMode === 'login' ? 'auth-toggle active' : 'auth-toggle'}
//             onClick={() => setAuthMode('login')}
//           >
//             Login
//           </button>
//           <button
//             type="button"
//             className={authMode === 'signup' ? 'auth-toggle active' : 'auth-toggle'}
//             onClick={() => setAuthMode('signup')}
//           >
//             Signup
//           </button>
//         </div>

//         <label className="field">
//           Username
//           <input
//             type="text"
//             value={authMode === 'login' ? loginForm.username : signupForm.username}
//             onChange={(event) => {
//               const value = event.target.value
//               if (authMode === 'login') {
//                 setLoginForm((prev) => ({ ...prev, username: value }))
//                 return
//               }
//               setSignupForm((prev) => ({ ...prev, username: value }))
//             }}
//             autoComplete="username"
//             required
//           />
//         </label>

//         <label className="field">
//           Password
//           <input
//             type="password"
//             value={authMode === 'login' ? loginForm.password : signupForm.password}
//             onChange={(event) => {
//               const value = event.target.value
//               if (authMode === 'login') {
//                 setLoginForm((prev) => ({ ...prev, password: value }))
//                 return
//               }
//               setSignupForm((prev) => ({ ...prev, password: value }))
//             }}
//             autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
//             required
//           />
//         </label>

//         {authMode === 'signup' ? (
//           <label className="field">
//             Confirm Password
//             <input
//               type="password"
//               value={signupForm.confirmPassword}
//               onChange={(event) => setSignupForm((prev) => ({ ...prev, confirmPassword: event.target.value }))}
//               autoComplete="new-password"
//               required
//             />
//           </label>
//         ) : null}

//         {activeError ? <div className="error-banner">{activeError}</div> : null}

//         <button type="submit" className="primary-btn" disabled={activeLoading}>
//           {activeLoading ? (authMode === 'login' ? 'Signing in...' : 'Creating account...') : authMode === 'login' ? 'Login' : 'Create Account'}
//         </button>

//         <small className="auth-note">
//           {authMode === 'login' ? 'Use your existing account credentials.' : 'Create an account and start immediately.'}
//         </small>
//       </form>
//     </div>
//   )
// }

// export default function App() {
//   const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '')
//   const [username, setUsername] = useState(() => localStorage.getItem(USER_KEY) || '')
//   const [authChecking, setAuthChecking] = useState(Boolean(localStorage.getItem(TOKEN_KEY)))
//   const [authMode, setAuthMode] = useState('login')
//   const [loginForm, setLoginForm] = useState({ username: '', password: '' })
//   const [signupForm, setSignupForm] = useState({ username: '', password: '', confirmPassword: '' })
//   const [loginLoading, setLoginLoading] = useState(false)
//   const [signupLoading, setSignupLoading] = useState(false)
//   const [loginError, setLoginError] = useState('')
//   const [signupError, setSignupError] = useState('')

//   const [tab, setTab] = useState('assessment')
//   const [organ, setOrgan] = useState('skin')
//   const [questionnaire, setQuestionnaire] = useState(initialQuestionnaire)
  
//   // Fix - Fixed threshould manually changing by user issue
//   // const [severityThreshold, setSeverityThreshold] = useState(0.72)

//   const severityThreshold = 0.72;

//   // Fix end here
  

//   const [files, setFiles] = useState([])
//   const [dragActive, setDragActive] = useState(false)
//   const [manualLoading, setManualLoading] = useState(false)
//   const [manualError, setManualError] = useState('')
//   const [manualBundle, setManualBundle] = useState(null)

//   const [cameraActive, setCameraActive] = useState(false)
//   const [cameraError, setCameraError] = useState('')
//   const [liveBusy, setLiveBusy] = useState(false)
//   const [liveError, setLiveError] = useState('')
//   const [liveBundle, setLiveBundle] = useState(null)
//   const [autoAnalyze, setAutoAnalyze] = useState(false)
//   const [liveIntervalSec, setLiveIntervalSec] = useState(6)

//   const [latestPredictionId, setLatestPredictionId] = useState('')
//   const [chatInput, setChatInput] = useState('')
//   const [chatMessages, setChatMessages] = useState([
//     {
//       id: `msg-${Date.now()}`,
//       role: 'assistant',
//       text: 'Ask about severity, diet, or next steps after running an analysis.'
//     }
//   ])
//   const [chatLoading, setChatLoading] = useState(false)
//   const [chatError, setChatError] = useState('')

//   const videoRef = useRef(null)
//   const canvasRef = useRef(null)
//   const streamRef = useRef(null)
//   const timerRef = useRef(null)
//   const liveBusyRef = useRef(false)

//   const selectedNames = useMemo(() => files.map((file) => file.name).join(', '), [files])

//   function handleLogout() {
//     if (timerRef.current) {
//       clearInterval(timerRef.current)
//       timerRef.current = null
//     }
//     if (streamRef.current) {
//       streamRef.current.getTracks().forEach((track) => track.stop())
//       streamRef.current = null
//     }
//     if (videoRef.current) {
//       videoRef.current.srcObject = null
//     }
//     setCameraActive(false)
//     setAutoAnalyze(false)
//     setToken('')
//     setUsername('')
//     setAuthChecking(false)
//     setLatestPredictionId('')
//     localStorage.removeItem(TOKEN_KEY)
//     localStorage.removeItem(USER_KEY)
//   }

//   function startSession(payload) {
//     setToken(payload.access_token)
//     setUsername(payload.username)
//     localStorage.setItem(TOKEN_KEY, payload.access_token)
//     localStorage.setItem(USER_KEY, payload.username)
//     setChatMessages([
//       {
//         id: `msg-${Date.now()}`,
//         role: 'assistant',
//         text: 'Session active. Ask for severity interpretation, food strategy, or escalation guidance.'
//       }
//     ])
//   }

//   async function apiRequest(path, options = {}) {
//     const { method = 'GET', body, includeAuth = true } = options
//     const headers = {}
//     let payload = body

//     if (includeAuth && token) {
//       headers.Authorization = `Bearer ${token}`
//     }
//     if (payload && !(payload instanceof FormData)) {
//       headers['Content-Type'] = 'application/json'
//       payload = JSON.stringify(payload)
//     }

//     const response = await fetch(`${API_BASE}${path}`, {
//       method,
//       headers,
//       body: payload
//     })

//     const raw = await response.text()
//     let parsed = null
//     if (raw) {
//       try {
//         parsed = JSON.parse(raw)
//       } catch {
//         parsed = raw
//       }
//     }

//     if (!response.ok) {
//       if (response.status === 401 && includeAuth) {
//         handleLogout()
//       }
//       const detail =
//         typeof parsed === 'string'
//           ? parsed
//           : parsed?.detail || `Request failed (${response.status})`
//       throw new Error(detail)
//     }
//     return parsed
//   }

//   function updateQ(field, value) {
//     setQuestionnaire((prev) => ({ ...prev, [field]: value }))
//   }

//   function pickFiles(fileList) {
//     const valid = Array.from(fileList || []).filter((file) => file.type.startsWith('image/'))
//     setFiles(valid)
//   }

//   async function runAnalysis(images) {
//     const answers = await apiRequest('/answers', {
//       method: 'POST',
//       body: questionnaire
//     })

//     const formData = new FormData()
//     images.forEach((file) => formData.append('images', file))
//     formData.append('questionnaire', JSON.stringify(questionnaire))
//     formData.append('session_id', answers.session_id)
//     formData.append('organ', organ)
//     formData.append('severity_threshold', String(severityThreshold))

//     const prediction = await apiRequest('/predict', {
//       method: 'POST',
//       body: formData
//     })

//     const result = await apiRequest(`/result/${prediction.prediction_id}`)
//     const diet = await apiRequest(`/diet/${prediction.prediction_id}`)

//     setLatestPredictionId(prediction.prediction_id)
//     return {
//       prediction,
//       result: result.payload,
//       diet: diet.recommendation,
//       createdAt: new Date().toISOString()
//     }
//   }

//   async function handleLogin(event) {
//     event.preventDefault()
//     setLoginError('')
//     setLoginLoading(true)
//     try {
//       const payload = await apiRequest('/auth/login', {
//         method: 'POST',
//         body: loginForm,
//         includeAuth: false
//       })
//       startSession(payload)
//       setLoginForm({ username: '', password: '' })
//     } catch (error) {
//       setLoginError(error.message || String(error))
//     } finally {
//       setLoginLoading(false)
//     }
//   }

//   async function handleSignup(event) {
//     event.preventDefault()
//     setSignupError('')

//     if (signupForm.password !== signupForm.confirmPassword) {
//       setSignupError('Password and confirm password do not match.')
//       return
//     }

//     setSignupLoading(true)
//     try {
//       const payload = await apiRequest('/auth/signup', {
//         method: 'POST',
//         body: {
//           username: signupForm.username,
//           password: signupForm.password
//         },
//         includeAuth: false
//       })
//       startSession(payload)
//       setSignupForm({ username: '', password: '', confirmPassword: '' })
//     } catch (error) {
//       setSignupError(error.message || String(error))
//     } finally {
//       setSignupLoading(false)
//     }
//   }

//   async function handleManualSubmit(event) {
//     event.preventDefault()
//     if (!files.length) {
//       setManualError('Please upload at least one image.')
//       return
//     }

//     setManualError('')
//     setManualLoading(true)
//     try {
//       const bundle = await runAnalysis(files)
//       setManualBundle(bundle)
//     } catch (error) {
//       setManualError(error.message || String(error))
//     } finally {
//       setManualLoading(false)
//     }
//   }

//   async function startCamera() {
//     setCameraError('')
//     try {
//       if (streamRef.current) {
//         streamRef.current.getTracks().forEach((track) => track.stop())
//         streamRef.current = null
//       }

//       let stream = null
//       try {
//         stream = await navigator.mediaDevices.getUserMedia({
//           video: {
//             facingMode: { ideal: 'user' },
//             width: { ideal: 1280 },
//             height: { ideal: 720 }
//           },
//           audio: false
//         })
//       } catch {
//         stream = await navigator.mediaDevices.getUserMedia({
//           video: true,
//           audio: false
//         })
//       }

//       streamRef.current = stream
//       setCameraActive(true)
//     } catch (error) {
//       setCameraError(error.message || 'Camera permission denied or unavailable.')
//       setCameraActive(false)
//     }
//   }

//   function stopCamera() {
//     setAutoAnalyze(false)
//     if (timerRef.current) {
//       clearInterval(timerRef.current)
//       timerRef.current = null
//     }
//     if (streamRef.current) {
//       streamRef.current.getTracks().forEach((track) => track.stop())
//       streamRef.current = null
//     }
//     if (videoRef.current) {
//       videoRef.current.srcObject = null
//     }
//     setCameraActive(false)
//   }

//   function captureFrameAsFile() {
//     return new Promise((resolve, reject) => {
//       const video = videoRef.current
//       const canvas = canvasRef.current
//       if (!video || !canvas) {
//         reject(new Error('Camera is not ready.'))
//         return
//       }

//       const width = video.videoWidth || 1280
//       const height = video.videoHeight || 720
//       canvas.width = width
//       canvas.height = height

//       const context = canvas.getContext('2d')
//       if (!context) {
//         reject(new Error('Canvas context unavailable.'))
//         return
//       }
//       context.drawImage(video, 0, 0, width, height)

//       canvas.toBlob(
//         (blob) => {
//           if (!blob) {
//             reject(new Error('Could not capture camera frame.'))
//             return
//           }
//           resolve(new File([blob], `live-${Date.now()}.jpg`, { type: 'image/jpeg' }))
//         },
//         'image/jpeg',
//         0.92
//       )
//     })
//   }

//   async function runLiveAnalysis() {
//     if (!cameraActive) {
//       setLiveError('Start the camera before running live analysis.')
//       return
//     }
//     if (liveBusyRef.current) {
//       return
//     }

//     setLiveError('')
//     setLiveBusy(true)
//     try {
//       const frame = await captureFrameAsFile()
//       const bundle = await runAnalysis([frame])
//       setLiveBundle(bundle)
//     } catch (error) {
//       setLiveError(error.message || String(error))
//     } finally {
//       setLiveBusy(false)
//     }
//   }

//   async function sendMessage(customText = null) {
//     const message = (customText || chatInput).trim()
//     if (!message || chatLoading) {
//       return
//     }

//     setChatError('')
//     setChatInput('')
//     setChatMessages((prev) => [
//       ...prev,
//       {
//         id: `msg-${Date.now()}-${Math.random()}`,
//         role: 'user',
//         text: message
//       }
//     ])

//     setChatLoading(true)
//     try {
//       const payload = await apiRequest('/chat', {
//         method: 'POST',
//         body: {
//           message,
//           prediction_id: latestPredictionId || null,
//           severity_threshold: severityThreshold
//         }
//       })
//       setChatMessages((prev) => [
//         ...prev,
//         {
//           id: `msg-${Date.now()}-${Math.random()}`,
//           role: 'assistant',
//           text: payload.reply,
//           guidance: payload.guidance || [],
//           severityAlert: Boolean(payload.severity_alert)
//         }
//       ])
//     } catch (error) {
//       setChatError(error.message || String(error))
//     } finally {
//       setChatLoading(false)
//     }
//   }

//   useEffect(() => {
//     setLoginError('')
//     setSignupError('')
//   }, [authMode])

//   useEffect(() => {
//     if (!token) {
//       setAuthChecking(false)
//       return
//     }

//     let cancelled = false
//     ;(async () => {
//       try {
//         const profile = await apiRequest('/auth/me')
//         if (cancelled) {
//           return
//         }
//         setUsername(profile.username)
//       } catch {
//         if (!cancelled) {
//           handleLogout()
//         }
//       } finally {
//         if (!cancelled) {
//           setAuthChecking(false)
//         }
//       }
//     })()

//     return () => {
//       cancelled = true
//     }
//   }, [token])

//   useEffect(() => {
//     if (!cameraActive || tab !== 'live') {
//       return
//     }

//     const video = videoRef.current
//     const stream = streamRef.current
//     if (!video || !stream) {
//       return
//     }

//     if (video.srcObject !== stream) {
//       video.srcObject = stream
//     }

//     const playPromise = video.play()
//     if (playPromise && typeof playPromise.catch === 'function') {
//       playPromise.catch((error) => {
//         setCameraError(`Unable to render camera preview: ${error.message || error}`)
//       })
//     }
//   }, [cameraActive, tab])

//   useEffect(() => {
//     liveBusyRef.current = liveBusy
//   }, [liveBusy])

//   useEffect(() => {
//     if (!autoAnalyze || !cameraActive) {
//       if (timerRef.current) {
//         clearInterval(timerRef.current)
//         timerRef.current = null
//       }
//       return
//     }

//     const seconds = Math.max(3, Number(liveIntervalSec) || 3)
//     timerRef.current = setInterval(() => {
//       runLiveAnalysis()
//     }, seconds * 1000)

//     return () => {
//       if (timerRef.current) {
//         clearInterval(timerRef.current)
//         timerRef.current = null
//       }
//     }
//   }, [autoAnalyze, cameraActive, liveIntervalSec, organ, questionnaire, severityThreshold, token])

//   useEffect(() => {
//     return () => {
//       if (timerRef.current) {
//         clearInterval(timerRef.current)
//       }
//       if (streamRef.current) {
//         streamRef.current.getTracks().forEach((track) => track.stop())
//       }
//     }
//   }, [])

//   if (!token) {
//     return (
//       <LoginView
//         authMode={authMode}
//         setAuthMode={setAuthMode}
//         loginForm={loginForm}
//         setLoginForm={setLoginForm}
//         signupForm={signupForm}
//         setSignupForm={setSignupForm}
//         loginLoading={loginLoading}
//         signupLoading={signupLoading}
//         loginError={loginError}
//         signupError={signupError}
//         onLogin={handleLogin}
//         onSignup={handleSignup}
//       />
//     )
//   }

//   if (authChecking) {
//     return (
//       <div className="login-shell">
//         <div className="login-card">
//           <h1>Checking session...</h1>
//           <p>Please wait while we validate your credentials.</p>
//         </div>
//       </div>
//     )
//   }

//   return (
//     <div className="app-shell">
//       <div className="ambient ambient-left" />
//       <div className="ambient ambient-right" />

//       <header className="topbar">
//         <div>
//           <h1>Vitamin Deficiency Intelligence Hub</h1>
//           <p>Authenticated multimodal triage with live camera monitoring and contextual AI guidance.</p>
//         </div>
//         <div className="topbar-side">
//           <div className="threshold-box">
//             <label>
//               Severity Alert Threshold <strong>{toPercent(severityThreshold)}</strong>
//             </label>
            
//             {/* Fix - preventing user to manually adjust threshould */}
            
//             {/* <input
//               type="range"
//               min="0.4"
//               max="0.95"
//               step="0.01"
//               value={severityThreshold}
//               onChange={(event) => setSeverityThreshold(Number(event.target.value))}
//             /> */}

//             {/* Fix end here */}
            
//           </div>
//           <div className="account-box">
//             <span>{username}</span>
//             <button type="button" className="ghost-btn" onClick={handleLogout}>
//               Logout
//             </button>
//           </div>
//         </div>
//       </header>

//       <nav className="tabbar">
//         <button
//           type="button"
//           className={tab === 'assessment' ? 'tab active' : 'tab'}
//           onClick={() => setTab('assessment')}
//         >
//           Upload Assessment
//         </button>
//         <button
//           type="button"
//           className={tab === 'live' ? 'tab active' : 'tab'}
//           onClick={() => setTab('live')}
//         >
//           Live Camera
//         </button>
//         <button
//           type="button"
//           className={tab === 'assistant' ? 'tab active' : 'tab'}
//           onClick={() => setTab('assistant')}
//         >
//           AI Assistant
//         </button>
//       </nav>

//       {tab === 'assessment' && (
//         <section className="tab-panel">
//           <form className="card form-card" onSubmit={handleManualSubmit}>
//             <h2>Image + Questionnaire Analysis</h2>
//             <div className="form-grid">
//               <label className="field">
//                 Image Region
//                 <select value={organ} onChange={(event) => setOrgan(event.target.value)}>
//                   <option value="eye">Eye</option>
//                   <option value="nail">Nail</option>
//                   <option value="skin">Skin</option>
//                 </select>
//               </label>
//               <label className="field">
//                 Diet Type
//                 <select value={questionnaire.diet_type} onChange={(event) => updateQ('diet_type', event.target.value)}>
//                   <option value="omnivore">Omnivore</option>
//                   <option value="vegetarian">Vegetarian</option>
//                   <option value="vegan">Vegan</option>
//                 </select>
//               </label>
//               <label className="field">
//                 Fatigue
//                 <select value={questionnaire.fatigue} onChange={(event) => updateQ('fatigue', Number(event.target.value))}>
//                   <option value={0}>No</option>
//                   <option value={1}>Yes</option>
//                 </select>
//               </label>
//               <label className="field">
//                 Pregnancy
//                 <select value={questionnaire.pregnancy} onChange={(event) => updateQ('pregnancy', Number(event.target.value))}>
//                   <option value={0}>No</option>
//                   <option value={1}>Yes</option>
//                 </select>
//               </label>
//               <label className="field">
//                 Sunlight Exposure (hours/day)
//                 <input
//                   type="number"
//                   min="0"
//                   max="16"
//                   step="0.5"
//                   value={questionnaire.sunlight_exposure}
//                   onChange={(event) => updateQ('sunlight_exposure', Number(event.target.value))}
//                 />
//               </label>
//               <label className="field">
//                 Medications (count)
//                 <input
//                   type="number"
//                   min="0"
//                   max="10"
//                   value={questionnaire.medications}
//                   onChange={(event) => updateQ('medications', Number(event.target.value))}
//                 />
//               </label>
//               <label className="field">
//                 Chronic Illness
//                 <select
//                   value={questionnaire.chronic_illness}
//                   onChange={(event) => updateQ('chronic_illness', Number(event.target.value))}
//                 >
//                   <option value={0}>No</option>
//                   <option value={1}>Yes</option>
//                 </select>
//               </label>
//               <label className="field">
//                 Allergies
//                 <select value={questionnaire.allergies} onChange={(event) => updateQ('allergies', Number(event.target.value))}>
//                   <option value={0}>No</option>
//                   <option value={1}>Yes</option>
//                 </select>
//               </label>
//               <label className="field">
//                 Vegetarian
//                 <select value={questionnaire.vegetarian} onChange={(event) => updateQ('vegetarian', Number(event.target.value))}>
//                   <option value={0}>No</option>
//                   <option value={1}>Yes</option>
//                 </select>
//               </label>
//               <label className="field">
//                 Lactose Intolerance
//                 <select
//                   value={questionnaire.lactose_intolerance}
//                   onChange={(event) => updateQ('lactose_intolerance', Number(event.target.value))}
//                 >
//                   <option value={0}>No</option>
//                   <option value={1}>Yes</option>
//                 </select>
//               </label>
//             </div>

//             <div
//               className={`dropzone ${dragActive ? 'dropzone-active' : ''}`}
//               onDragOver={(event) => {
//                 event.preventDefault()
//                 setDragActive(true)
//               }}
//               onDragLeave={() => setDragActive(false)}
//               onDrop={(event) => {
//                 event.preventDefault()
//                 setDragActive(false)
//                 pickFiles(event.dataTransfer.files)
//               }}
//             >
//               <input type="file" accept="image/*" multiple onChange={(event) => pickFiles(event.target.files)} />
//               <p>Drag and drop images here or click to browse.</p>
//               <small>{selectedNames || 'No images selected'}</small>
//             </div>

//             {manualError ? <div className="error-banner">{manualError}</div> : null}

//             <button type="submit" className="primary-btn" disabled={manualLoading}>
//               {manualLoading ? 'Analyzing...' : 'Run End-to-End Analysis'}
//             </button>
//           </form>

//           <AnalysisResult bundle={manualBundle} title="Upload Analysis Result" />
//         </section>
//       )}

//       {tab === 'live' && (
//         <section className="tab-panel">
//           <article className="card form-card">
//             <h2>Live Camera Analysis</h2>
//             <p className="muted">Capture real-time frames and trigger severity alerts using your configured threshold.</p>
//             <div className="camera-frame">
//               {cameraActive ? (
//                 <video ref={videoRef} autoPlay playsInline muted />
//               ) : (
//                 <div className="camera-placeholder">Camera offline. Start to begin live analysis.</div>
//               )}
//             </div>
//             <canvas ref={canvasRef} className="hidden-canvas" />

//             <div className="camera-actions">
//               <button type="button" className="ghost-btn" onClick={startCamera} disabled={cameraActive}>
//                 Start Camera
//               </button>
//               <button type="button" className="ghost-btn" onClick={stopCamera} disabled={!cameraActive}>
//                 Stop Camera
//               </button>
//               <button type="button" className="primary-btn" onClick={runLiveAnalysis} disabled={!cameraActive || liveBusy}>
//                 {liveBusy ? 'Analyzing frame...' : 'Analyze Current Frame'}
//               </button>
//             </div>

//             <div className="auto-row">
//               <label className="switch-field">
//                 <input
//                   type="checkbox"
//                   checked={autoAnalyze}
//                   onChange={(event) => setAutoAnalyze(event.target.checked)}
//                   disabled={!cameraActive}
//                 />
//                 Auto-analyze
//               </label>
//               <label className="field interval-field">
//                 Interval (seconds)
//                 <input
//                   type="number"
//                   min="3"
//                   max="60"
//                   value={liveIntervalSec}
//                   onChange={(event) => setLiveIntervalSec(Number(event.target.value))}
//                 />
//               </label>
//             </div>

//             {cameraError ? <div className="error-banner">{cameraError}</div> : null}
//             {liveError ? <div className="error-banner">{liveError}</div> : null}
//           </article>

//           <AnalysisResult bundle={liveBundle} title="Live Analysis Result" />
//         </section>
//       )}

//       {tab === 'assistant' && (
//         <section className="tab-panel single-column">
//           <article className="card chat-card">
//             <div className="chat-head">
//               <h2>Clinical Assistant</h2>
//               <span className="muted">Prediction context: {latestPredictionId || 'none yet'}</span>
//             </div>

//             <div className="prompt-row">
//               {quickPrompts.map((prompt) => (
//                 <button key={prompt} type="button" className="chip-btn" onClick={() => sendMessage(prompt)}>
//                   {prompt}
//                 </button>
//               ))}
//             </div>

//             <div className="chat-log">
//               {chatMessages.map((entry) => (
//                 <div key={entry.id} className={`chat-bubble ${entry.role === 'user' ? 'bubble-user' : 'bubble-assistant'}`}>
//                   <p>{entry.text}</p>
//                   {entry.guidance?.length ? (
//                     <ul className="guidance-list">
//                       {entry.guidance.map((tip) => (
//                         <li key={`${entry.id}-${tip}`}>{tip}</li>
//                       ))}
//                     </ul>
//                   ) : null}
//                   {entry.severityAlert ? <small className="alert-text">Severity alert is active.</small> : null}
//                 </div>
//               ))}
//               {chatLoading ? <div className="chat-bubble bubble-assistant">Thinking...</div> : null}
//             </div>

//             <form
//               className="chat-compose"
//               onSubmit={(event) => {
//                 event.preventDefault()
//                 sendMessage()
//               }}
//             >
//               <input
//                 type="text"
//                 value={chatInput}
//                 onChange={(event) => setChatInput(event.target.value)}
//                 placeholder="Ask about severity, food strategy, or escalation..."
//               />
//               <button type="submit" className="primary-btn" disabled={chatLoading}>
//                 Send
//               </button>
//             </form>

//             {chatError ? <div className="error-banner">{chatError}</div> : null}
//           </article>
//         </section>
//       )}
//     </div>
//   )
// }





import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const TOKEN_KEY = 'vitamin_ai_token'
const USER_KEY = 'vitamin_ai_username'

const initialQuestionnaire = {
  fatigue: 1,
  diet_type: 'omnivore',
  vegetarian: 0,
  pregnancy: 0,
  sunlight_exposure: 2,
  medications: 0,
  chronic_illness: 0,
  allergies: 0,
  lactose_intolerance: 0
}

const quickPrompts = [
  'What does my severity mean?',
  'Give me a practical food plan for today',
  'When should I consult a specialist?'
]

const SEVERITY_THRESHOLD = 0.72

function toPercent(value) {
  return `${Math.round((value || 0) * 100)}%`
}

function AnalysisResult({ bundle, title }) {
  if (!bundle) {
    return (
      <article className="card result-empty">
        <h3>{title}</h3>
        <p>
          Run an analysis to view prediction, severity alerts, food
          recommendations, and heatmaps.
        </p>
      </article>
    )
  }

  const prediction = bundle.prediction || {}

  const severity = prediction.severity || 0
  const threshold = prediction.severity_threshold || SEVERITY_THRESHOLD

  let statusLabel = 'OK'
  let statusClass = 'status-ok'

  if (severity >= threshold) {
    statusLabel = 'Severe'
    statusClass = 'status-alert'
  } else if (severity >= threshold - 0.15) {
    statusLabel = 'Mild'
    statusClass = 'status-warning'
  }

  const result = bundle.result || {}
  const diet = bundle.diet || {}

  const probabilities = Object.entries(prediction.probabilities || {}).sort(
    (a, b) => b[1] - a[1]
  )

  const rankedFoods = (diet.ranked_foods || []).slice(0, 10)
  const mealPlan = Object.entries(diet.meal_plan || {})
  const heatmaps = result.heatmaps || []

  return (
    <div className="result-stack">
      {statusLabel === 'Severe' && (
        <div className="critical-alert-banner">
          <div className="alert-content">
            <h2>⚠️ CRITICAL SEVERITY DETECTED</h2>
            <p>
              Your analysis indicates a high probability of severe vitamin
              deficiency. Please consult a medical professional immediately.
            </p>
          </div>
        </div>
      )}

      <article className="card">
        <div className="card-head">
          <h3>{title}</h3>
          <span className={`status-pill ${statusClass}`}>{statusLabel}</span>
        </div>

        <p className="muted">
          Updated: {new Date(bundle.createdAt).toLocaleString()}
        </p>

        <div className="metrics-grid">
          <div className="metric-block">
            <label>Predicted class</label>
            <strong>{prediction.predicted_class || 'n/a'}</strong>
          </div>
          <div className="metric-block">
            <label>Confidence</label>
            <strong>{toPercent(prediction.confidence)}</strong>
          </div>
          <div className="metric-block">
            <label>Severity</label>
            <strong>{toPercent(prediction.severity)}</strong>
          </div>
          <div className="metric-block">
            <label>Threshold</label>
            <strong>{toPercent(prediction.severity_threshold)}</strong>
          </div>
        </div>

        <div className="gauge-shell">
          <div
            className="gauge-fill"
            style={{ width: toPercent(prediction.severity) }}
          />
          <span>Severity {toPercent(prediction.severity)}</span>
        </div>
      </article>

      {statusLabel !== 'OK' ? (
        <>
          <article className="card">
            <h3>Probability Breakdown</h3>
            <ul className="compact-list">
              {probabilities.map(([label, value]) => (
                <li key={label}>
                  <span>{label}</span>
                  <strong>{toPercent(value)}</strong>
                </li>
              ))}
            </ul>
          </article>

          <article className="card">
            <h3>Top Recommended Foods</h3>
            {rankedFoods.length === 0 ? (
              <p className="muted">Diet recommendation not available.</p>
            ) : (
              <ul className="compact-list">
                {rankedFoods.map((item) => (
                  <li key={`${item.food_name}-${item.source_dataset}`}>
                    <span>{item.food_name}</span>
                    <strong>{item.score?.toFixed(3)}</strong>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article className="card">
            <h3>Meal Plan</h3>
            {mealPlan.length === 0 ? (
              <p className="muted">Meal plan unavailable.</p>
            ) : (
              <ul className="compact-list">
                {mealPlan.map(([slot, item]) => (
                  <li key={slot}>
                    <span>{slot}</span>
                    <strong>{item?.food_name || 'n/a'}</strong>
                  </li>
                ))}
              </ul>
            )}
            {diet.medical_advice && (
              <p
                className={`advice ${
                  diet.consult_specialist ? 'advice-alert' : 'advice-ok'
                }`}
              >
                {diet.medical_advice}
              </p>
            )}
          </article>
        </>
      ) : (
        <article className="card status-ok-message">
          <h3>Results: Healthy</h3>
          <p>
            Your indicators are within normal ranges. No specific dietary
            changes are recommended at this time. Maintain your current healthy
            lifestyle.
          </p>
        </article>
      )}

      <article className="card heatmap-card">
        <h3>Grad-CAM Viewer</h3>
        {heatmaps.length === 0 ? (
          <p className="muted">No heatmaps generated for this run.</p>
        ) : (
          <div className="heatmap-grid">
            {heatmaps.map((hm) => (
              <div className="heatmap-pair" key={hm.image_id}>
                <figure>
                  <img
                    src={`data:image/jpeg;base64,${hm.base_b64}`}
                    alt="Base frame"
                  />
                  <figcaption>Base</figcaption>
                </figure>
                <figure>
                  <img
                    src={`data:image/jpeg;base64,${hm.overlay_b64}`}
                    alt="Grad-CAM overlay"
                  />
                  <figcaption>Grad-CAM</figcaption>
                </figure>
              </div>
            ))}
          </div>
        )}
      </article>
    </div>
  )
}

function LoginView({
  authMode,
  setAuthMode,
  loginForm,
  setLoginForm,
  signupForm,
  setSignupForm,
  loginLoading,
  signupLoading,
  loginError,
  signupError,
  onLogin,
  onSignup
}) {
  const activeError = authMode === 'login' ? loginError : signupError
  const activeLoading = authMode === 'login' ? loginLoading : signupLoading
  const activeSubmit = authMode === 'login' ? onLogin : onSignup

  return (
    <div className="login-shell">
      <div className="aura aura-one" />
      <div className="aura aura-two" />
      <form className="login-card" onSubmit={activeSubmit}>
        <h1>Vitamin AI Clinical Console</h1>
        <p>
          Secure access for image + questionnaire analysis, live camera triage,
          and AI-guided nutrition planning.
        </p>

        <div className="auth-switch">
          <button
            type="button"
            className={authMode === 'login' ? 'auth-toggle active' : 'auth-toggle'}
            onClick={() => setAuthMode('login')}
          >
            Login
          </button>
          <button
            type="button"
            className={authMode === 'signup' ? 'auth-toggle active' : 'auth-toggle'}
            onClick={() => setAuthMode('signup')}
          >
            Signup
          </button>
        </div>

        <label className="field">
          Username
          <input
            type="text"
            value={authMode === 'login' ? loginForm.username : signupForm.username}
            onChange={(event) => {
              const value = event.target.value
              if (authMode === 'login') {
                setLoginForm((prev) => ({ ...prev, username: value }))
                return
              }
              setSignupForm((prev) => ({ ...prev, username: value }))
            }}
            autoComplete="username"
            required
          />
        </label>

        <label className="field">
          Password
          <input
            type="password"
            value={authMode === 'login' ? loginForm.password : signupForm.password}
            onChange={(event) => {
              const value = event.target.value
              if (authMode === 'login') {
                setLoginForm((prev) => ({ ...prev, password: value }))
                return
              }
              setSignupForm((prev) => ({ ...prev, password: event.target.value }))
            }}
            autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
            required
          />
        </label>

        {authMode === 'signup' && (
          <label className="field">
            Confirm Password
            <input
              type="password"
              value={signupForm.confirmPassword}
              onChange={(event) =>
                setSignupForm((prev) => ({
                  ...prev,
                  confirmPassword: event.target.value
                }))
              }
              autoComplete="new-password"
              required
            />
          </label>
        )}

        {activeError && <div className="error-banner">{activeError}</div>}

        <button type="submit" className="primary-btn" disabled={activeLoading}>
          {activeLoading
            ? authMode === 'login'
              ? 'Signing in...'
              : 'Creating account...'
            : authMode === 'login'
            ? 'Login'
            : 'Create Account'}
        </button>

        <small className="auth-note">
          {authMode === 'login'
            ? 'Use your existing account credentials.'
            : 'Create an account and start immediately.'}
        </small>
      </form>
    </div>
  )
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '')
  const [username, setUsername] = useState(
    () => localStorage.getItem(USER_KEY) || ''
  )
  const [authChecking, setAuthChecking] = useState(
    Boolean(localStorage.getItem(TOKEN_KEY))
  )
  const [authMode, setAuthMode] = useState('login')
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [signupForm, setSignupForm] = useState({
    username: '',
    password: '',
    confirmPassword: ''
  })
  const [loginLoading, setLoginLoading] = useState(false)
  const [signupLoading, setSignupLoading] = useState(false)
  const [loginError, setLoginError] = useState('')
  const [signupError, setSignupError] = useState('')

  const [tab, setTab] = useState('assessment')
  const [organ, setOrgan] = useState('skin')
  const [questionnaire, setQuestionnaire] = useState(initialQuestionnaire)

  const severityThreshold = SEVERITY_THRESHOLD

  const [files, setFiles] = useState([])
  const [dragActive, setDragActive] = useState(false)
  const [manualLoading, setManualLoading] = useState(false)
  const [manualError, setManualError] = useState('')
  const [manualBundle, setManualBundle] = useState(null)

  const [cameraActive, setCameraActive] = useState(false)
  const [cameraError, setCameraError] = useState('')
  const [liveBusy, setLiveBusy] = useState(false)
  const [liveError, setLiveError] = useState('')
  const [liveBundle, setLiveBundle] = useState(null)
  const [autoAnalyze, setAutoAnalyze] = useState(false)
  const [liveIntervalSec, setLiveIntervalSec] = useState(6)

  const [latestPredictionId, setLatestPredictionId] = useState('')
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState([
    {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      text: 'Ask about severity, diet, or next steps after running an analysis.'
    }
  ])
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')

  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const timerRef = useRef(null)
  const liveBusyRef = useRef(false)

  const selectedNames = useMemo(
    () => files.map((file) => file.name).join(', '),
    [files]
  )

  const handleLogout = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setCameraActive(false)
    setAutoAnalyze(false)
    setToken('')
    setUsername('')
    setAuthChecking(false)
    setLatestPredictionId('')
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }, [])

  function startSession(payload) {
    setToken(payload.access_token)
    setUsername(payload.username)
    localStorage.setItem(TOKEN_KEY, payload.access_token)
    localStorage.setItem(USER_KEY, payload.username)
    setChatMessages([
      {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        text: 'Session active. Ask for severity interpretation, food strategy, or escalation guidance.'
      }
    ])
  }

  const apiRequest = useCallback(
    async (path, options = {}) => {
      const { method = 'GET', body, includeAuth = true } = options
      const headers = {}
      let payload = body

      if (includeAuth && token) {
        headers.Authorization = `Bearer ${token}`
      }
      if (payload && !(payload instanceof FormData)) {
        headers['Content-Type'] = 'application/json'
        payload = JSON.stringify(payload)
      }

      const response = await fetch(`${API_BASE}${path}`, {
        method,
        headers,
        body: payload
      })

      const raw = await response.text()
      let parsed = null
      if (raw) {
        try {
          parsed = JSON.parse(raw)
        } catch {
          parsed = raw
        }
      }

      if (!response.ok) {
        if (response.status === 401 && includeAuth) {
          handleLogout()
        }
        const detail =
          typeof parsed === 'string'
            ? parsed
            : parsed?.detail || `Request failed (${response.status})`
        throw new Error(detail)
      }
      return parsed
    },
    [token, handleLogout]
  )

  function updateQ(field, value) {
    setQuestionnaire((prev) => ({ ...prev, [field]: value }))
  }

  function pickFiles(fileList) {
    const valid = Array.from(fileList || []).filter((file) =>
      file.type.startsWith('image/')
    )
    setFiles(valid)
  }

  const runAnalysis = useCallback(
    async (images) => {
      const answers = await apiRequest('/answers', {
        method: 'POST',
        body: questionnaire
      })

      const formData = new FormData()
      images.forEach((file) => formData.append('images', file))
      formData.append('questionnaire', JSON.stringify(questionnaire))
      formData.append('session_id', answers.session_id)
      formData.append('organ', organ)
      formData.append('severity_threshold', String(severityThreshold))

      const prediction = await apiRequest('/predict', {
        method: 'POST',
        body: formData
      })

      const result = await apiRequest(`/result/${prediction.prediction_id}`)
      const diet = await apiRequest(`/diet/${prediction.prediction_id}`)

      setLatestPredictionId(prediction.prediction_id)
      return {
        prediction,
        result: result.payload,
        diet: diet.recommendation,
        createdAt: new Date().toISOString()
      }
    },
    [apiRequest, organ, questionnaire, severityThreshold]
  )

  async function handleLogin(event) {
    event.preventDefault()
    setLoginError('')
    setLoginLoading(true)
    try {
      const payload = await apiRequest('/auth/login', {
        method: 'POST',
        body: loginForm,
        includeAuth: false
      })
      startSession(payload)
      setLoginForm({ username: '', password: '' })
    } catch (error) {
      setLoginError(error.message || String(error))
    } finally {
      setLoginLoading(false)
    }
  }

  async function handleSignup(event) {
    event.preventDefault()
    setSignupError('')

    if (signupForm.password !== signupForm.confirmPassword) {
      setSignupError('Password and confirm password do not match.')
      return
    }

    setSignupLoading(true)
    try {
      const payload = await apiRequest('/auth/signup', {
        method: 'POST',
        body: {
          username: signupForm.username,
          password: signupForm.password
        },
        includeAuth: false
      })
      startSession(payload)
      setSignupForm({ username: '', password: '', confirmPassword: '' })
    } catch (error) {
      setSignupError(error.message || String(error))
    } finally {
      setSignupLoading(false)
    }
  }

  async function handleManualSubmit(event) {
    event.preventDefault()
    if (!files.length) {
      setManualError('Please upload at least one image.')
      return
    }

    setManualError('')
    setManualLoading(true)
    try {
      const bundle = await runAnalysis(files)
      setManualBundle(bundle)
    } catch (error) {
      setManualError(error.message || String(error))
    } finally {
      setManualLoading(false)
    }
  }

  async function startCamera() {
    setCameraError('')
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
      }

      let stream = null
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: 'user' },
            width: { ideal: 1280 },
            height: { ideal: 720 }
          },
          audio: false
        })
      } catch {
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false
        })
      }

      streamRef.current = stream
      setCameraActive(true)
    } catch (error) {
      setCameraError(error.message || 'Camera permission denied or unavailable.')
      setCameraActive(false)
    }
  }

  function stopCamera() {
    setAutoAnalyze(false)
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setCameraActive(false)
  }

  function captureFrameAsFile() {
    return new Promise((resolve, reject) => {
      const video = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas) {
        reject(new Error('Camera is not ready.'))
        return
      }

      const width = video.videoWidth || 1280
      const height = video.videoHeight || 720
      canvas.width = width
      canvas.height = height

      const context = canvas.getContext('2d')
      if (!context) {
        reject(new Error('Canvas context unavailable.'))
        return
      }
      context.drawImage(video, 0, 0, width, height)

      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('Could not capture camera frame.'))
            return
          }
          resolve(new File([blob], `live-${Date.now()}.jpg`, { type: 'image/jpeg' }))
        },
        'image/jpeg',
        0.92
      )
    })
  }

  const runLiveAnalysis = useCallback(async () => {
    if (!cameraActive) {
      setLiveError('Start the camera before running live analysis.')
      return
    }
    if (liveBusyRef.current) {
      return
    }

    setLiveError('')
    setLiveBusy(true)
    try {
      const frame = await captureFrameAsFile()
      const bundle = await runAnalysis([frame])
      setLiveBundle(bundle)
    } catch (error) {
      setLiveError(error.message || String(error))
    } finally {
      setLiveBusy(false)
    }
  }, [cameraActive, runAnalysis])

  async function sendMessage(customText = null) {
    const message = (customText || chatInput).trim()
    if (!message || chatLoading) {
      return
    }

    setChatError('')
    setChatInput('')
    setChatMessages((prev) => [
      ...prev,
      {
        id: `msg-${Date.now()}-${Math.random()}`,
        role: 'user',
        text: message
      }
    ])

    setChatLoading(true)
    try {
      const payload = await apiRequest('/chat', {
        method: 'POST',
        body: {
          message,
          prediction_id: latestPredictionId || null,
          severity_threshold: severityThreshold
        }
      })
      setChatMessages((prev) => [
        ...prev,
        {
          id: `msg-${Date.now()}-${Math.random()}`,
          role: 'assistant',
          text: payload.reply,
          guidance: payload.guidance || [],
          severityAlert: Boolean(payload.severity_alert)
        }
      ])
    } catch (error) {
      setChatError(error.message || String(error))
    } finally {
      setChatLoading(false)
    }
  }

  useEffect(() => {
    setLoginError('')
    setSignupError('')
  }, [authMode])

  useEffect(() => {
    if (!token) {
      setAuthChecking(false)
      return
    }

    let cancelled = false
    ;(async () => {
      try {
        const profile = await apiRequest('/auth/me')
        if (cancelled) return
        setUsername(profile.username)
      } catch {
        if (!cancelled) handleLogout()
      } finally {
        if (!cancelled) setAuthChecking(false)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [token, apiRequest, handleLogout])

  useEffect(() => {
    if (!cameraActive || tab !== 'live') return

    const video = videoRef.current
    const stream = streamRef.current
    if (!video || !stream) return

    if (video.srcObject !== stream) {
      video.srcObject = stream
    }

    const playPromise = video.play()
    if (playPromise && typeof playPromise.catch === 'function') {
      playPromise.catch((error) => {
        setCameraError(
          `Unable to render camera preview: ${error.message || error}`
        )
      })
    }
  }, [cameraActive, tab])

  useEffect(() => {
    liveBusyRef.current = liveBusy
  }, [liveBusy])

  useEffect(() => {
    if (!autoAnalyze || !cameraActive) {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
      return
    }

    const seconds = Math.max(3, Number(liveIntervalSec) || 3)
    timerRef.current = setInterval(() => {
      runLiveAnalysis()
    }, seconds * 1000)

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [autoAnalyze, cameraActive, liveIntervalSec, runLiveAnalysis])

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
      }
    }
  }, [])

  if (!token) {
    return (
      <LoginView
        authMode={authMode}
        setAuthMode={setAuthMode}
        loginForm={loginForm}
        setLoginForm={setLoginForm}
        signupForm={signupForm}
        setSignupForm={setSignupForm}
        loginLoading={loginLoading}
        signupLoading={signupLoading}
        loginError={loginError}
        signupError={signupError}
        onLogin={handleLogin}
        onSignup={handleSignup}
      />
    )
  }

  if (authChecking) {
    return (
      <div className="login-shell">
        <div className="login-card">
          <h1>Checking session...</h1>
          <p>Please wait while we validate your credentials.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />

      <header className="topbar">
        <div>
          <h1>Vitamin Deficiency Intelligence Hub</h1>
          <p>
            Authenticated multimodal triage with live camera monitoring and
            contextual AI guidance.
          </p>
        </div>
        <div className="topbar-side">
          <div className="threshold-box">
            <label>
              Severity Alert Threshold{' '}
              <strong>{toPercent(severityThreshold)}</strong>
            </label>
          </div>
          <div className="account-box">
            <span>{username}</span>
            <button type="button" className="ghost-btn" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </div>
      </header>

      <nav className="tabbar">
        <button
          type="button"
          className={tab === 'assessment' ? 'tab active' : 'tab'}
          onClick={() => setTab('assessment')}
        >
          Upload Assessment
        </button>
        <button
          type="button"
          className={tab === 'live' ? 'tab active' : 'tab'}
          onClick={() => setTab('live')}
        >
          Live Camera
        </button>
        <button
          type="button"
          className={tab === 'assistant' ? 'tab active' : 'tab'}
          onClick={() => setTab('assistant')}
        >
          AI Assistant
        </button>
      </nav>

      {tab === 'assessment' && (
        <section className="tab-panel">
          <form className="card form-card" onSubmit={handleManualSubmit}>
            <h2>Image + Questionnaire Analysis</h2>
            <div className="form-grid">
              <label className="field">
                Image Region
                <select
                  value={organ}
                  onChange={(event) => setOrgan(event.target.value)}
                >
                  <option value="eye">Eye</option>
                  <option value="nail">Nail</option>
                  <option value="skin">Skin</option>
                </select>
              </label>
              <label className="field">
                Diet Type
                <select
                  value={questionnaire.diet_type}
                  onChange={(event) => updateQ('diet_type', event.target.value)}
                >
                  <option value="omnivore">Omnivore</option>
                  <option value="vegetarian">Vegetarian</option>
                  <option value="vegan">Vegan</option>
                </select>
              </label>
              <label className="field">
                Fatigue
                <select
                  value={questionnaire.fatigue}
                  onChange={(event) =>
                    updateQ('fatigue', Number(event.target.value))
                  }
                >
                  <option value={0}>No</option>
                  <option value={1}>Yes</option>
                </select>
              </label>
              <label className="field">
                Pregnancy
                <select
                  value={questionnaire.pregnancy}
                  onChange={(event) =>
                    updateQ('pregnancy', Number(event.target.value))
                  }
                >
                  <option value={0}>No</option>
                  <option value={1}>Yes</option>
                </select>
              </label>
              <label className="field">
                Sunlight Exposure (hours/day)
                <input
                  type="number"
                  min="0"
                  max="16"
                  step="0.5"
                  value={questionnaire.sunlight_exposure}
                  onChange={(event) =>
                    updateQ('sunlight_exposure', Number(event.target.value))
                  }
                />
              </label>
              <label className="field">
                Medications (count)
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={questionnaire.medications}
                  onChange={(event) =>
                    updateQ('medications', Number(event.target.value))
                  }
                />
              </label>
              <label className="field">
                Chronic Illness
                <select
                  value={questionnaire.chronic_illness}
                  onChange={(event) =>
                    updateQ('chronic_illness', Number(event.target.value))
                  }
                >
                  <option value={0}>No</option>
                  <option value={1}>Yes</option>
                </select>
              </label>
              <label className="field">
                Allergies
                <select
                  value={questionnaire.allergies}
                  onChange={(event) =>
                    updateQ('allergies', Number(event.target.value))
                  }
                >
                  <option value={0}>No</option>
                  <option value={1}>Yes</option>
                </select>
              </label>
              <label className="field">
                Vegetarian
                <select
                  value={questionnaire.vegetarian}
                  onChange={(event) =>
                    updateQ('vegetarian', Number(event.target.value))
                  }
                >
                  <option value={0}>No</option>
                  <option value={1}>Yes</option>
                </select>
              </label>
              <label className="field">
                Lactose Intolerance
                <select
                  value={questionnaire.lactose_intolerance}
                  onChange={(event) =>
                    updateQ('lactose_intolerance', Number(event.target.value))
                  }
                >
                  <option value={0}>No</option>
                  <option value={1}>Yes</option>
                </select>
              </label>
            </div>

            <div
              className={`dropzone ${dragActive ? 'dropzone-active' : ''}`}
              onDragOver={(event) => {
                event.preventDefault()
                setDragActive(true)
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={(event) => {
                event.preventDefault()
                setDragActive(false)
                pickFiles(event.dataTransfer.files)
              }}
            >
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={(event) => pickFiles(event.target.files)}
              />
              <p>Drag and drop images here or click to browse.</p>
              <small>{selectedNames || 'No images selected'}</small>
            </div>

            {manualError && (
              <div className="error-banner">{manualError}</div>
            )}

            <button
              type="submit"
              className="primary-btn"
              disabled={manualLoading}
            >
              {manualLoading ? 'Analyzing...' : 'Run End-to-End Analysis'}
            </button>
          </form>

          <AnalysisResult bundle={manualBundle} title="Upload Analysis Result" />
        </section>
      )}

      {tab === 'live' && (
        <section className="tab-panel">
          <article className="card form-card">
            <h2>Live Camera Analysis</h2>
            <p className="muted">
              Capture real-time frames and trigger severity alerts using your
              configured threshold.
            </p>
            <div className="camera-frame">
              {cameraActive ? (
                <video ref={videoRef} autoPlay playsInline muted />
              ) : (
                <div className="camera-placeholder">
                  Camera offline. Start to begin live analysis.
                </div>
              )}
            </div>
            <canvas ref={canvasRef} className="hidden-canvas" />

            <div className="camera-actions">
              <button
                type="button"
                className="ghost-btn"
                onClick={startCamera}
                disabled={cameraActive}
              >
                Start Camera
              </button>
              <button
                type="button"
                className="ghost-btn"
                onClick={stopCamera}
                disabled={!cameraActive}
              >
                Stop Camera
              </button>
              <button
                type="button"
                className="primary-btn"
                onClick={runLiveAnalysis}
                disabled={!cameraActive || liveBusy}
              >
                {liveBusy ? 'Analyzing frame...' : 'Analyze Current Frame'}
              </button>
            </div>

            <div className="auto-row">
              <label className="switch-field">
                <input
                  type="checkbox"
                  checked={autoAnalyze}
                  onChange={(event) => setAutoAnalyze(event.target.checked)}
                  disabled={!cameraActive}
                />
                Auto-analyze
              </label>
              <label className="field interval-field">
                Interval (seconds)
                <input
                  type="number"
                  min="3"
                  max="60"
                  value={liveIntervalSec}
                  onChange={(event) =>
                    setLiveIntervalSec(Number(event.target.value))
                  }
                />
              </label>
            </div>

            {cameraError && (
              <div className="error-banner">{cameraError}</div>
            )}
            {liveError && <div className="error-banner">{liveError}</div>}
          </article>

          <AnalysisResult bundle={liveBundle} title="Live Analysis Result" />
        </section>
      )}

      {tab === 'assistant' && (
        <section className="tab-panel single-column">
          <article className="card chat-card">
            <div className="chat-head">
              <h2>Clinical Assistant</h2>
              <span className="muted">
                Prediction context: {latestPredictionId || 'none yet'}
              </span>
            </div>

            <div className="prompt-row">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="chip-btn"
                  onClick={() => sendMessage(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>

            <div className="chat-log">
              {chatMessages.map((entry) => (
                <div
                  key={entry.id}
                  className={`chat-bubble ${
                    entry.role === 'user' ? 'bubble-user' : 'bubble-assistant'
                  }`}
                >
                  <p>{entry.text}</p>
                  {entry.guidance?.length ? (
                    <ul className="guidance-list">
                      {entry.guidance.map((tip) => (
                        <li key={`${entry.id}-${tip}`}>{tip}</li>
                      ))}
                    </ul>
                  ) : null}
                  {entry.severityAlert && (
                    <small className="alert-text">
                      Severity alert is active.
                    </small>
                  )}
                </div>
              ))}
              {chatLoading && (
                <div className="chat-bubble bubble-assistant">Thinking...</div>
              )}
            </div>

            <form
              className="chat-compose"
              onSubmit={(event) => {
                event.preventDefault()
                sendMessage()
              }}
            >
              <input
                type="text"
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                placeholder="Ask about severity, food strategy, or escalation..."
              />
              <button
                type="submit"
                className="primary-btn"
                disabled={chatLoading}
              >
                Send
              </button>
            </form>

            {chatError && <div className="error-banner">{chatError}</div>}
          </article>
        </section>
      )}
    </div>
  )
}
