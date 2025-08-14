
import axios from 'axios';

//const API_BASE_URL = 'http://35.219.54.8:8882';
const API_BASE_URL = 'http://localhost:8080'; // Your Frappe instance URL

/*
// --- HARDCODED API KEY & SECRET (FOR DEVELOPMENT ONLY) ---
const HARDCODED_API_KEY = '691dc30ced24013';//'2b7d7c65471aecf';
const HARDCODED_API_SECRET = 'c4c52d2694638d1';// '2fa510cb40c011b';
// ----------------------------------------------------------
*/

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Still needed for initial session login
});

// Remove the Expect header to prevent 417 errors with some servers/proxies
delete api.defaults.headers.common['Expect'];

/*
// Add a request interceptor to include the Authorization header for all requests
api.interceptors.request.use(config => {
  // Only add Authorization header if it's not the initial login request
  // and if hardcoded keys are available
  if (config.url !== '/api/method/login' && HARDCODED_API_KEY && HARDCODED_API_SECRET) {
    config.headers.Authorization = `token ${HARDCODED_API_KEY}:${HARDCODED_API_SECRET}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});
*/

interface LoginResponse {
  success: boolean;
  message?: string;
  salesName?: string;
  userId?: string;
}

export const login = async (username: string, password: string): Promise<LoginResponse> => {
  try {
    // Step 1: Perform standard username/password login to establish session
    const response = await api.post('/api/method/login', {
      usr: username,
      pwd: password,
    });

    if (response.status !== 200) {
      return { success: false, message: response.data.message || 'Login failed' };
    }

    // Step 2: After successful session login, use API Key to get user details
    // The interceptor will add the Authorization header for this request
    const userDetailsResponse = await api.get('/api/method/frappe.auth.get_logged_user');
    const userId = userDetailsResponse.data.message; // This should be the user's email/username

    if (userId) {
      // Frappe's get_logged_user returns 'Guest' if not logged in, or the user ID
      if (userId === 'Guest') {
        return { success: false, message: 'Login failed: User is Guest.' };
      }

      const employeeId = await getEmployeeId(userId);
      if (employeeId) {
        // You might want to add role validation here if needed
        return { success: true, salesName: employeeId, userId: userId };
      } else {
        return { success: false, message: 'Employee ID not found for this user.' };
      }
    } else {
      return { success: false, message: 'Failed to retrieve logged-in user details.' };
    }
  } catch (error: any) {
    console.error("Login error:", error.response?.data || error.message);
    return { success: false, message: error.response?.data?.message || 'An unexpected error occurred during login.' };
  }
};

interface VisitPlan {
  name: string; // Frappe DocType name (e.g., 'SVP0001')
  store_name: string;
  address: string;
  status: 'Draft' | 'Planned' | 'Checked In' | 'Completed' | 'Canceled';
  planned_visit_time?: string;
  checkin_time?: string;
  checkout_time?: string;
  latitude?: number;
  longitude?: number;
  photo_url?: string | null;
}

export const getVisitPlans = async (salesName: string): Promise<VisitPlan[]> => {
  try {
    const response = await api.get('/api/method/sales_monitor.api.get_sales_visit_plans', {
      params: { sales_name: salesName, date: new Date().toISOString().split('T')[0] },
    });
    return response.data.message || response.data.data || [];
  } catch (error: any) {
    console.error("Error fetching visit plans:", error.response?.data || error.message);
    throw new Error(error.response?.data?.message || 'Failed to fetch visit plans.');
  }
};

export const updateVisitPlanStatus = async (name: string, newStatus: 'Checked In' | 'Completed', data?: { latitude?: number, longitude?: number, photo_url?: string }): Promise<boolean> => {
  try {
    const payload: any = {
      name: name,
      new_status: newStatus,
    };
    if (data) {
      payload.latitude = data.latitude;
      payload.longitude = data.longitude;
      payload.photo_url = data.photo_url;
    }

    const response = await api.post('/api/method/sales_monitor.api.update_sales_visit_plan_status', payload);
    return response.data.message === 'Success';
  } catch (error: any) {
    console.error("Error updating visit plan status:", error.response?.data || error.message);
    throw new Error(error.response?.data?.message || 'Failed to update visit plan status.');
  }
};

export const getEmployeeId = async (userId: string): Promise<string | null> => {
  try {
    const response = await api.get('/api/method/sales_monitor.api.get_employee_id', {
      params: { user_id: userId },
    });
    return response.data.message || null;
  } catch (error: any) {
    console.error("Error fetching employee ID:", error.response?.data || error.message);
    throw new Error(error.response?.data?.message || 'Failed to fetch employee ID.');
  }
};

export const getOrderHistory = async (storeName: string): Promise<any[]> => {
  try {
    const response = await api.get('/api/method/sales_monitor.api.get_order_history', {
      params: { store_name: storeName },
    });
    return response.data.message || response.data.data || [];
  } catch (error: any) {
    console.error("Error fetching order history:", error.response?.data || error.message);
    throw new Error(error.response?.data?.message || 'Failed to fetch order history.');
  }
};

export const logout = async (): Promise<boolean> => {
  try {
    const response = await api.post('/api/method/logout');
    return response.data.message === 'Logged Out';
  } catch (error) {
    console.error("Error logging out:", error);
    return false;
  }
};
