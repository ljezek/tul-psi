import React from 'react';

const App: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-tul-blue rounded-2xl mb-6 text-white font-bold text-2xl">
          FM
        </div>
        <h1 className="text-4xl font-bold text-slate-800 mb-2">Katalog Projektů</h1>
        <p className="text-slate-500">Technická univerzita v Liberci</p>
      </div>
    </div>
  );
};

export default App;

