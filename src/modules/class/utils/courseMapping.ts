export interface CourseInfo {
  code: string;
  name: string;
}

const buildClasses = (prefix: string, code: string, name: string, count: number): Record<string, CourseInfo> => {
  const result: Record<string, CourseInfo> = {};
  for (let i = 1; i <= count; i++) {
    result[`${prefix}_${i}`] = { code, name: `${name} (Class ${i})` };
  }
  return result;
};

export const COURSE_MAPPING: Record<string, CourseInfo> = {
  ...buildClasses('AAA', 'PHI1006', 'Marxist-Leninist Philosophy', 8),
  ...buildClasses('BBB', 'PEC1008', 'Marxist-Leninist Political Economy', 10),
  ...buildClasses('CCC', 'HIS1001', 'History of the Communist Party of Vietnam', 8),
  ...buildClasses('DDD', 'POL1001', "Ho Chi Minh's Ideology", 8),
  ...buildClasses('EEE', 'PHI1002', 'Scientific Socialism', 8),
  ...buildClasses('FFF', 'FLF1107', 'English B1', 12),
  ...buildClasses('GGG', 'VNU1001', 'Introduction to Digital Technology and AI', 6),
  ...buildClasses('HHH', 'THL1057', 'State and Law', 6),
  ...buildClasses('III', 'UET.MAT1053', 'Linear Algebra for Engineers', 10),
  ...buildClasses('JJJ', 'UET.MAT1050', 'Calculus 1 for Engineers', 10),
  ...buildClasses('KKK', 'UET.MAT1051', 'Calculus 2 for Engineers', 10),
  ...buildClasses('LLL', 'UET.PHY1095', 'General Physics 1', 8),
  ...buildClasses('MMM', 'UET.PHY1096', 'General Physics 2', 8),
  ...buildClasses('NNN', 'UET.COM1050', 'Computational Thinking', 10),
  ...buildClasses('OOO', 'UET.MAT1052', 'Probability and Statistics', 8),
  ...buildClasses('PPP', 'UET.CS1058', 'Data Structures and Algorithms', 8),
  ...buildClasses('QQQ', 'UET.MAT1057', 'Discrete Mathematics', 8),
  ...buildClasses('RRR', 'UET.CS2043', 'Advanced Programming', 8),
  ...buildClasses('SSS', 'UET.IS2099', 'Database', 8),
  ...buildClasses('TTT', 'UET.CN2042', 'Computer Network', 8),
  ...buildClasses('UUU', 'UET.CS2045', 'Software Engineering', 8),
  ...buildClasses('VVV', 'UET.CS2046', 'Artificial Intelligence', 6),
  ...buildClasses('WWW', 'UET.IS2100', 'Fundamentals of Operating Systems', 6),
  ...buildClasses('XXX', 'UET.CE2021', 'Computer Architecture', 6),
  ...buildClasses('YYY', 'UET.CS3136', 'Machine Learning', 6),
  ...buildClasses('ZZZ', 'UET.IT3291', 'System Analysis and Design', 6),
  ...buildClasses('A01', 'UET.IT3294', 'Program Analysis and Testing', 6),
  ...buildClasses('A02', 'UET.IT3296', 'Advanced Topics in Information Technology', 6),
  ...buildClasses('A03', 'UET.CE2020', 'Systems Programming', 4),
  ...buildClasses('A04', 'UET.IT3289', 'Cross-platform Application Development', 4),
  ...buildClasses('A05', 'UET.IT3290', 'IT Project Management', 4),
  ...buildClasses('A06', 'UET.IT3292', 'Designing Large-scale Software Systems', 4),
  ...buildClasses('A07', 'UET.IT3297', 'AI Engineering', 4),
  ...buildClasses('A08', 'UET.IT3298', 'API Design and Implementation', 4),
  ...buildClasses('A09', 'UET.CS3152', 'User Interface and User Experience Design', 4),
  ...buildClasses('A10', 'UET.CS3144', 'Scientific Computing for Machine Learning', 4),
  ...buildClasses('A11', 'UET.CS3142', 'Natural Language Processing', 4),
  ...buildClasses('A12', 'UET.AI3056', 'Deep Learning', 4),
  ...buildClasses('A13', 'UET.CS3150', 'Image Processing and Computer Vision', 4),
  ...buildClasses('A14', 'UET.IS3278', 'Data Mining', 4),
  ...buildClasses('A15', 'UET.IS3276', 'Big Data Analytics', 4),
  ...buildClasses('A16', 'UET.IS3283', 'Business Intelligence', 4),
  ...buildClasses('A17', 'UET.IS3286', 'Business Analytics', 4),
  ...buildClasses('A18', 'UET.CN3124', 'Network Security', 4),
  ...buildClasses('A19', 'UET.CN3125', 'System Administration', 4),
  ...buildClasses('A20', 'UET.CN3134', 'Cloud Computing', 4),
};

export const getUetCourseInfo = (ouladModule: string): CourseInfo => {
  return COURSE_MAPPING[ouladModule] || { code: ouladModule, name: `Module ${ouladModule}` };
};