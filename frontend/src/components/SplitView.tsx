import React, { ReactNode } from 'react';

interface SplitViewProps {
  leftPanel: ReactNode;
  rightPanel: ReactNode;
}

export const SplitView: React.FC<SplitViewProps> = ({ leftPanel, rightPanel }) => {
  return (
    <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
      {/* Left Panel: Summary & Chat */}
      <section className="w-full lg:w-1/2 border-r border-stone-200 bg-white flex flex-col h-full overflow-hidden">
        {leftPanel}
      </section>

      {/* Right Panel: Interactive PDF Viewer */}
      <section className="w-full lg:w-1/2 bg-stone-100 flex flex-col h-full overflow-hidden">
        {rightPanel}
      </section>
    </div>
  );
};
