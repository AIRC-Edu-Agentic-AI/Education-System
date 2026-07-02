import express from 'express'
import cors from 'cors'
import { MongoClient } from 'mongodb'
import dotenv from 'dotenv'

dotenv.config()

const app = express()
const PORT = 8000

const MONGO_URI = process.env.MONGODB_URI
const CORS_ORIGIN = process.env.CORS_ORIGIN ?? 'http://localhost:5173'

if (!MONGO_URI) {
  console.error('Missing required env var: MONGODB_URI')
  process.exit(1)
}

const client = new MongoClient(MONGO_URI)
const db = client.db(process.env.MONGODB_DB ?? 'oulad_db')

app.use(cors({ origin: CORS_ORIGIN }))
app.use(express.json())

app.get('/api/index', async (_req, res) => {
  const courses = await db.collection("processed_courses").find({}, { projection: { students: 0 } }).toArray()
  const result = courses.map(c => ({
    module: c.module,
    module_name: c.module_name,
    presentation: c.presentation,
    presentation_name: c.presentation_name,
    course_length_days: c.num_weeks * 7,
    num_weeks: c.num_weeks,
    student_count: c.student_count
  }))
  res.json({ courses: result })
})

app.get('/api/course/:module/:presentation', async (req, res) => {
  const { module, presentation } = req.params
  const course = await db.collection("processed_courses").findOne(
    { module, presentation },
    { projection: { _id: 0 } }
  )
  if (!course) return res.status(404).json({ error: "Course not found" })

  const students = await db.collection("processed_students").find(
    { code_module: module, code_presentation: presentation },
    { projection: { _id: 0 } }
  ).toArray()

  res.json({ ...course, students })
})

app.get('/api/student/:module/:presentation/:student_id', async (req, res) => {
  const { module, presentation, student_id } = req.params
  const student = await db.collection("processed_students").findOne(
    { code_module: module, code_presentation: presentation, id_student: parseInt(student_id) },
    { projection: { _id: 0 } }
  )
  if (!student) return res.status(404).json({ error: "Student not found" })
  res.json(student)
})

// Schedules: store per-course schedules in collection `schedules`
app.get('/api/schedules/:module/:presentation', async (req, res) => {
  const { module, presentation } = req.params
  const doc = await db.collection('schedules').findOne({ module, presentation }, { projection: { _id: 0 } })
  if (!doc) return res.json({ schedules: [] })
  res.json({ schedules: doc.schedules ?? [] })
})

app.post('/api/schedules/:module/:presentation', async (req, res) => {
  const { module, presentation } = req.params
  const { schedules } = req.body
  if (!Array.isArray(schedules)) return res.status(400).json({ error: 'Invalid schedules payload' })

  await db.collection('schedules').updateOne(
    { module, presentation },
    { $set: { schedules } },
    { upsert: true }
  )

  res.json({ ok: true })
})

app.get('/api/schedules', async (_req, res) => {
  const allDoc = await db.collection('schedules_all').findOne({ _id: { $eq: 'all' } as any }, { projection: { _id: 0 } })
  if (allDoc && Array.isArray(allDoc.schedules)) {
    return res.json({ schedules: allDoc.schedules })
  }

  const docs = await db.collection('schedules').find({}, { projection: { _id: 0 } }).toArray()
  const schedules = docs.flatMap((doc) =>
    (doc.schedules ?? []).map((item: any) => ({
      ...item,
      module: doc.module,
      presentation: doc.presentation,
    }))
  )
  res.json({ schedules })
})

app.post('/api/schedules', async (req, res) => {
  const { schedules } = req.body
  if (!Array.isArray(schedules)) return res.status(400).json({ error: 'Invalid schedules payload' })

  await db.collection('schedules_all').updateOne(
    { _id: { $eq: 'all' } as any },
    { $set: { schedules } },
    { upsert: true }
  )

  res.json({ ok: true })
})

async function start() {
  await client.connect()
  console.log("Connected to MongoDB Atlas!")
  app.listen(PORT, () => console.log(`Server running on http://localhost:${PORT}`))
}

start()