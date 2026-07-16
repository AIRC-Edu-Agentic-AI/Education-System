export interface CourseInfo {
  code: string;
  name: string;
  semester?: string;
}

const ACTIVE_SEMESTERS = ['2023-1', '2023-2', '2024-1', '2024-2', '2025-1', '2025-2'];

const buildCourseSemesters = (
  code: string, 
  name: string, 
  semesters: string[] = ACTIVE_SEMESTERS
): Record<string, CourseInfo> => {
  const result: Record<string, CourseInfo> = {};
  for (const sem of semesters) {
    result[`${code}_${sem}`] = { code, name, semester: sem };
  }
  return result;
};

export const COURSE_MAPPING: Record<string, CourseInfo> = {
  ...buildCourseSemesters('PHI1006', 'Marxist-Leninist Philosophy'),
  ...buildCourseSemesters('PEC1008', 'Marxist-Leninist Political Economy'),
  ...buildCourseSemesters('HIS1001', 'History of the Communist Party of Vietnam'),
  ...buildCourseSemesters('POL1001', "Ho Chi Minh's Ideology"),
  ...buildCourseSemesters('PHI1002', 'Scientific Socialism'),
  ...buildCourseSemesters('FLF1107', 'English B1'),
  ...buildCourseSemesters('VNU1001', 'Introduction to Digital Technology and AI'),
  ...buildCourseSemesters('THL1057', 'State and Law'),
  ...buildCourseSemesters('UET.MAT1053', 'Linear Algebra for Engineers'),
  ...buildCourseSemesters('UET.MAT1050', 'Calculus 1 for Engineers'),
  ...buildCourseSemesters('UET.MAT1051', 'Calculus 2 for Engineers'),
  ...buildCourseSemesters('UET.PHY1095', 'General Physics 1'),
  ...buildCourseSemesters('UET.PHY1096', 'General Physics 2'),
  ...buildCourseSemesters('UET.COM1050', 'Computational Thinking'),
  ...buildCourseSemesters('UET.MAT1052', 'Probability and Statistics'),
  ...buildCourseSemesters('UET.CS1058', 'Data Structures and Algorithms'),
  ...buildCourseSemesters('UET.MAT1057', 'Discrete Mathematics'),
  ...buildCourseSemesters('UET.CS2043', 'Advanced Programming'),
  ...buildCourseSemesters('UET.IS2099', 'Database'),
  ...buildCourseSemesters('UET.CN2042', 'Computer Network'),
  ...buildCourseSemesters('UET.CS2045', 'Software Engineering'),
  ...buildCourseSemesters('UET.CS2046', 'Artificial Intelligence'),
  ...buildCourseSemesters('UET.IS2100', 'Fundamentals of Operating Systems'),
  ...buildCourseSemesters('UET.CE2021', 'Computer Architecture'),
  ...buildCourseSemesters('UET.CS3136', 'Machine Learning'),
  ...buildCourseSemesters('UET.IT3291', 'System Analysis and Design'),
  ...buildCourseSemesters('UET.IT3294', 'Program Analysis and Testing'),
  ...buildCourseSemesters('UET.IT3296', 'Advanced Topics in Information Technology'),
  ...buildCourseSemesters('UET.CE2020', 'Systems Programming'),
  ...buildCourseSemesters('UET.IT3289', 'Cross-platform Application Development'),
  ...buildCourseSemesters('UET.IT3290', 'IT Project Management'),
  ...buildCourseSemesters('UET.IT3292', 'Designing Large-scale Software Systems'),
  ...buildCourseSemesters('UET.IT3297', 'AI Engineering'),
  ...buildCourseSemesters('UET.IT3298', 'API Design and Implementation'),
  ...buildCourseSemesters('UET.CS3152', 'User Interface and User Experience Design'),
  ...buildCourseSemesters('UET.CS3144', 'Scientific Computing for Machine Learning'),
  ...buildCourseSemesters('UET.CS3142', 'Natural Language Processing'),
  ...buildCourseSemesters('UET.AI3056', 'Deep Learning'),
  ...buildCourseSemesters('UET.CS3150', 'Image Processing and Computer Vision'),
  ...buildCourseSemesters('UET.IS3278', 'Data Mining'),
  ...buildCourseSemesters('UET.IS3276', 'Big Data Analytics'),
  ...buildCourseSemesters('UET.IS3283', 'Business Intelligence'),
  ...buildCourseSemesters('UET.IS3286', 'Business Analytics'),
  ...buildCourseSemesters('UET.CN3124', 'Network Security'),
  ...buildCourseSemesters('UET.CN3125', 'System Administration'),
  ...buildCourseSemesters('UET.CN3134', 'Cloud Computing'),
  ...buildCourseSemesters('FLF1108', 'English B2'),
  ...buildCourseSemesters('UET.CS2020', 'Object-Oriented Programming'),
  ...buildCourseSemesters('UET.IS2001', 'E-Commerce'),
  ...buildCourseSemesters('UET.CS3111', 'Web Application Development'),
  ...buildCourseSemesters('UET.CS3112', 'Mobile Application Development'),
  ...buildCourseSemesters('UET.CE3012', 'Embedded Systems'),
  ...buildCourseSemesters('UET.CE3015', 'Internet of Things'),
  ...buildCourseSemesters('UET.CN3001', 'Cryptography and Network Security'),
  ...buildCourseSemesters('UET.CN3005', 'Ethical Hacking'),
  ...buildCourseSemesters('UET.CS3001', 'Computer Graphics'),
  ...buildCourseSemesters('UET.CS3005', 'Game Development'),
  ...buildCourseSemesters('UET.IT3001', 'Information Retrieval'),
  ...buildCourseSemesters('UET.IT3002', 'Semantic Web'),
  ...buildCourseSemesters('UET.CS3515', 'Software Testing & Quality Assurance'),
  ...buildCourseSemesters('PE1001', 'Physical Education'),
  ...buildCourseSemesters('DEF1001', 'National Defense Education'),
  ...buildCourseSemesters('UET.IT4001', 'Enterprise Internship'),
  ...buildCourseSemesters('UET.IT4002', 'Graduation Thesis')
};

export const MODULE_TRANSLATOR: Record<string, string> = {
  'AAA': 'PHI1006',
  'BBB': 'PEC1008',
  'CCC': 'HIS1001',
  'DDD': 'POL1001',
  'EEE': 'PHI1002',
  'FFF': 'FLF1107',
  'GGG': 'VNU1001',
  'HHH': 'THL1057',
  'III': 'UET.MAT1053',
  'JJJ': 'UET.MAT1050',
  'KKK': 'UET.MAT1051',
  'LLL': 'UET.PHY1095',
  'MMM': 'UET.PHY1096',
  'NNN': 'UET.COM1050',
  'OOO': 'UET.MAT1052',
  'PPP': 'UET.CS1058',
  'QQQ': 'UET.MAT1057',
  'RRR': 'UET.CS2043',
  'SSS': 'UET.IS2099',
  'TTT': 'UET.CN2042',
  'UUU': 'UET.CS2045',
  'VVV': 'UET.CS2046',
  'WWW': 'UET.IS2100',
  'XXX': 'UET.CE2021',
  'YYY': 'UET.CS3136',
  'ZZZ': 'UET.IT3291'
};

export const getUetCourseInfo = (ouladModule: string): CourseInfo => {
  
  const uetCode = MODULE_TRANSLATOR[ouladModule] || ouladModule;

  const matchedKey = Object.keys(COURSE_MAPPING).find(key => key.startsWith(`${uetCode}_`));

  if (matchedKey) {
    return COURSE_MAPPING[matchedKey];
  }


  return { 
    code: uetCode, 
    name: `Course ${uetCode}` 
  };
};
export const TERM_TRANSLATOR: Record<string, string> = {
  '2013B': '2023-1',
  '2013J': '2023-2',
  '2014B': '2024-1',
  '2014J': '2024-2',
};