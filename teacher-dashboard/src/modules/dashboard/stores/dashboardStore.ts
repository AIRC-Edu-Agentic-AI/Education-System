import { create } from 'zustand';

export const useDashboardStore = create((set) => ({
  // Dữ liệu mô phỏng theo từng cặp (Module_Presentation)
  courseDataMap: {
    'AAA_2013J': {
      assignments: [{ id: 1, title: "AAA Assignment: Intro to AI", dueDate: "Week 4" }],
      resources: [{ id: 1, name: "AAA Syllabus.pdf", type: "PDF" }],
      schedules: [{ id: 1, activity: "AAA Lecture", time: "Monday 9:00 AM" }]
    },
    'BBB_2014J': {
      assignments: [{ id: 2, title: "BBB Quiz: Statistics", dueDate: "Week 6" }],
      resources: [{ id: 2, name: "BBB Guide.pdf", type: "PDF" }],
      schedules: [{ id: 2, activity: "BBB Lab Session", time: "Friday 2:00 PM" }]
    }
  },

  // Hàm lấy dữ liệu dựa trên Module và Presentation đang chọn
  getCourseData: (module: string, presentation: string) => {
    const key = `${module}_${presentation}`;
    // @ts-ignore
    const data = useDashboardStore.getState().courseDataMap[key];
    
    // Nếu không tìm thấy dữ liệu cho lớp đó, trả về mảng rỗng thay vì lỗi
    return data || { assignments: [], resources: [], schedules: [] };
  }
}));