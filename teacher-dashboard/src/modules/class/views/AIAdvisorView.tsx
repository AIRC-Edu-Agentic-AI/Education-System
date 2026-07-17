import React, { useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'

export const AIAdvisorView = () => {
  const [input, setInput] = useState('');
  const [chat, setChat] = useState<{role: string, content: string}[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const newChat = [...chat, { role: 'user', content: input }];
    setChat(newChat);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      });
      
      const data = await res.json();
      
      if (data.reply) {
        setChat([...newChat, { role: 'ai', content: data.reply }]);
      } else {
        setChat([...newChat, { role: 'ai', content: 'Lỗi: Không nhận được phản hồi từ AI.' }]);
      }
    } catch (err) {
      console.error(err);
      setChat([...newChat, { role: 'ai', content: 'Lỗi kết nối đến Backend Server.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[80vh] p-6 bg-gray-50">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">AI Advisor - Tư vấn học tập</h2>
      
      {/* Khung hiển thị chat */}
      <div className="flex-1 overflow-y-auto mb-4 p-4 border rounded-lg bg-white shadow-inner">
        {chat.length === 0 && (
          <div className="text-center text-gray-400 mt-10">
            Hãy đặt câu hỏi về lộ trình học hoặc tình trạng của học sinh...
          </div>
        )}
        
        {chat.map((msg, idx) => (
          <div key={idx} className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[70%] p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-200 text-gray-800 rounded-bl-none'}`}>
              {msg.content}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-200 text-gray-800 p-3 rounded-lg rounded-bl-none animate-pulse">
              AI đang phân tích dữ liệu...
            </div>
          </div>
        )}
      </div>
      
      {/* Khung nhập liệu */}
      <div className="flex gap-2">
        <input
          type="text"
          className="flex-1 p-3 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ví dụ: Lên lộ trình ôn tập môn Python cho học sinh yếu..."
          disabled={isLoading}
        />
        <button 
          className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-sm hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
          onClick={handleSend}
          disabled={isLoading}
        >
          Gửi
        </button>
      </div>
    </div>
  );
};