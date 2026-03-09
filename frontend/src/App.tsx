import { Routes, Route } from 'react-router-dom';
import { SignIn, SignUp } from '@clerk/clerk-react';
import { ToastProvider } from './components/Toast';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import HomePage from './routes/index';
import BookDetailPage from './routes/book.$id';
import LoansPage from './routes/loans';
import HistoryPage from './routes/history';
import FinesPage from './routes/fines';
import MyReviewsPage from './routes/reviews';
import AIAssistantPage from './routes/ai-assistant';
import AdminLayout from './routes/admin/layout';
import AdminDashboard from './routes/admin/index';
import AdminBooksPage from './routes/admin/books';
import AdminUsersPage from './routes/admin/users';
import AdminUserDetail from './routes/admin/users.$id';
import AdminFinesPage from './routes/admin/fines';

function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route element={<ErrorBoundary><Layout /></ErrorBoundary>}>
          <Route index element={<HomePage />} />
          <Route path="/books/:id" element={<BookDetailPage />} />
          <Route
            path="/loans"
            element={
              <ProtectedRoute>
                <LoansPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/fines"
            element={
              <ProtectedRoute>
                <FinesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reviews"
            element={
              <ProtectedRoute>
                <MyReviewsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai-assistant"
            element={
              <ProtectedRoute>
                <AIAssistantPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sign-in/*"
            element={
              <div className="flex justify-center py-16">
                <SignIn routing="path" path="/sign-in" />
              </div>
            }
          />
          <Route
            path="/sign-up/*"
            element={
              <div className="flex justify-center py-16">
                <SignUp routing="path" path="/sign-up" />
              </div>
            }
          />
        </Route>
        <Route
          path="/admin"
          element={
            <ErrorBoundary>
              <ProtectedRoute adminOnly>
                <AdminLayout />
              </ProtectedRoute>
            </ErrorBoundary>
          }
        >
          <Route index element={<AdminDashboard />} />
          <Route path="books" element={<AdminBooksPage />} />
          <Route path="users" element={<AdminUsersPage />} />
          <Route path="users/:id" element={<AdminUserDetail />} />
          <Route path="fines" element={<AdminFinesPage />} />
        </Route>
      </Routes>
    </ToastProvider>
  );
}

export default App;
