import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';

const RootLayout = () => {
  const location = useLocation();
  const isChat = location.pathname === '/chat';

  return (
    <div className="root-layout">
      {!isChat && <div className="nebula-background" />}
      <div className="relative z-10 w-full h-full">
        <Outlet />
      </div>
    </div>
  );
};

export default RootLayout;
