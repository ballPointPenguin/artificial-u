import type { Component } from 'solid-js';
import { Button } from '@kobalte/core';

const App: Component = () => {
  return (
    <div class="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-4">
      <h1 class="text-4xl font-bold mb-8">Kobalte + Tailwind CSS</h1>

      <Button.Root
        class="px-6 py-3 
               bg-blue-600 
               hover:bg-blue-700 
               text-white 
               font-semibold 
               rounded-md 
               focus:outline-none 
               focus:ring-2 
               focus:ring-blue-500 
               focus:ring-opacity-50 
               transition-colors 
               duration-150 
               data-[pressed]:bg-blue-800
               data-[disabled]:opacity-50
               data-[disabled]:cursor-not-allowed"
      >
        Kobalte Button
      </Button.Root>

      <Button.Root
        class="mt-4 px-6 py-3 
               bg-gray-600 
               text-white 
               font-semibold 
               rounded-md 
               focus:outline-none 
               focus:ring-2 
               focus:ring-gray-500 
               focus:ring-opacity-50 
               transition-colors 
               duration-150 
               data-[pressed]:bg-gray-800
               data-[disabled]:opacity-50
               data-[disabled]:cursor-not-allowed"
        disabled
      >
        Disabled Button
      </Button.Root>

    </div>
  );
};

export default App;
