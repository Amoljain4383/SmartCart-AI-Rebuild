import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';
import AdminRoute from '../components/AdminRoute';
import * as AuthContextModule from '../context/AuthContext';

describe('Route Protection Guards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('ProtectedRoute redirects unauthenticated visitors to /login', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      isAuthenticated: false,
      isAdmin: false,
      loading: false,
      user: null,
    });

    render(
      <MemoryRouter initialEntries={['/checkout']}>
        <Routes>
          <Route
            path="/checkout"
            element={
              <ProtectedRoute>
                <div>Secret Checkout Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page Redirected</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Login Page Redirected')).toBeInTheDocument();
    expect(screen.queryByText('Secret Checkout Content')).not.toBeInTheDocument();
  });

  it('ProtectedRoute renders children when authenticated', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      isAuthenticated: true,
      isAdmin: false,
      loading: false,
      user: { id: 'u1', role: 'user' },
    });

    render(
      <MemoryRouter initialEntries={['/checkout']}>
        <Routes>
          <Route
            path="/checkout"
            element={
              <ProtectedRoute>
                <div>Secret Checkout Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Secret Checkout Content')).toBeInTheDocument();
  });

  it('AdminRoute blocks standard users (role="user") and redirects to home /', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      isAuthenticated: true,
      isAdmin: false,
      loading: false,
      user: { id: 'u1', role: 'user' },
    });

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <div>Restricted Admin Portal</div>
              </AdminRoute>
            }
          />
          <Route path="/" element={<div>Home Page Redirected</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Home Page Redirected')).toBeInTheDocument();
    expect(screen.queryByText('Restricted Admin Portal')).not.toBeInTheDocument();
  });

  it('AdminRoute renders children when user is role="admin"', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      isAuthenticated: true,
      isAdmin: true,
      loading: false,
      user: { id: 'a1', role: 'admin' },
    });

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <div>Restricted Admin Portal</div>
              </AdminRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Restricted Admin Portal')).toBeInTheDocument();
  });
});
