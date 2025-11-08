import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import VideoPlayerPage from '@/pages/VideoPlayerPage';
import SubmissionsPage from '@/pages/SubmissionsPage';
import { ToastProvider } from '@/hooks/useToast';
import './App.css';

function App() {
  return (
    <ToastProvider>
      <Router>
        <Routes>
          <Route path="/" element={<MainLayout />} />
          <Route path="/video-player" element={<VideoPlayerPage />} />
          <Route path="/submissions" element={<SubmissionsPage />} />
        </Routes>
      </Router>
    </ToastProvider>
  );
}

export default App;
