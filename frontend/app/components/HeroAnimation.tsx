'use client';

import { FileText, Sparkles, Code2, ArrowRight } from 'lucide-react';

export default function HeroAnimation() {
  return (
    <div className="relative w-full max-w-4xl mx-auto py-12">
      <div className="flex items-center justify-between gap-4">
        {/* Clinical Note */}
        <div className="flex-1 animate-fade-in">
          <div className="bg-white rounded-lg shadow-lg border-2 border-gray-200 p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center gap-3 mb-3">
              <FileText className="w-8 h-8 text-gray-700" />
              <h3 className="font-semibold text-gray-900">Clinical Note</h3>
            </div>
            <div className="text-sm text-gray-600 space-y-1">
              <p className="font-mono text-xs bg-gray-50 p-2 rounded">
                "Patient presents with <span className="text-blue-600 font-semibold">type 2 diabetes</span> and <span className="text-blue-600 font-semibold">hypertension</span>..."
              </p>
            </div>
          </div>
        </div>

        {/* Arrow 1 */}
        <div className="flex-shrink-0 animate-pulse-slow">
          <ArrowRight className="w-8 h-8 text-nuvii-blue" />
        </div>

        {/* AI Processing */}
        <div className="flex-1 animate-fade-in animation-delay-300">
          <div className="bg-gradient-to-br from-blue-50 to-teal-50 rounded-lg shadow-lg border-2 border-nuvii-blue p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center gap-3 mb-3">
              <Sparkles className="w-8 h-8 text-nuvii-blue animate-pulse" />
              <h3 className="font-semibold text-gray-900">AI Processing</h3>
            </div>
            <div className="text-sm text-gray-600">
              <p className="text-center font-semibold text-nuvii-blue">Analyzing...</p>
              <div className="mt-2 space-y-1">
                <div className="h-2 bg-nuvii-blue/20 rounded-full overflow-hidden">
                  <div className="h-full bg-nuvii-blue rounded-full animate-progress-bar"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Arrow 2 */}
        <div className="flex-shrink-0 animate-pulse-slow animation-delay-300">
          <ArrowRight className="w-8 h-8 text-nuvii-blue" />
        </div>

        {/* Medical Codes */}
        <div className="flex-1 animate-fade-in animation-delay-600">
          <div className="bg-white rounded-lg shadow-lg border-2 border-nuvii-teal p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-center gap-3 mb-3">
              <Code2 className="w-8 h-8 text-nuvii-teal" />
              <h3 className="font-semibold text-gray-900">Medical Codes</h3>
            </div>
            <div className="text-sm space-y-2">
              <div className="bg-teal-50 px-3 py-2 rounded border border-teal-200">
                <p className="font-mono font-bold text-nuvii-teal">E11.9</p>
                <p className="text-xs text-gray-600">Type 2 diabetes</p>
              </div>
              <div className="bg-teal-50 px-3 py-2 rounded border border-teal-200">
                <p className="font-mono font-bold text-nuvii-teal">I10</p>
                <p className="text-xs text-gray-600">Hypertension</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes pulse-slow {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.6;
            transform: scale(1.1);
          }
        }

        @keyframes progress-bar {
          0% {
            width: 0%;
          }
          100% {
            width: 100%;
          }
        }

        .animate-fade-in {
          animation: fade-in 0.8s ease-out forwards;
        }

        .animate-pulse-slow {
          animation: pulse-slow 2s ease-in-out infinite;
        }

        .animate-progress-bar {
          animation: progress-bar 2s ease-in-out infinite;
        }

        .animation-delay-300 {
          animation-delay: 0.3s;
        }

        .animation-delay-600 {
          animation-delay: 0.6s;
        }
      `}</style>
    </div>
  );
}
