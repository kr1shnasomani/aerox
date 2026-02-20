import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-[#0f0f23]">
      <Sidebar />
      <main className="ml-64 flex-1 p-8 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
