# Smart Timetable Generator - Technical Specification

## 1. Genetic Algorithm Implementation Details

### 1.1 Chromosome Encoding

```python
class TimetableChromosome:
    """
    Represents a complete timetable solution.
    Structure: 3D array [class][day][period] = {teacher, subject, room}
    """
    def __init__(self, num_classes, num_days, num_periods):
        self.num_classes = num_classes
        self.num_days = num_days  # Typically 5 or 6
        self.num_periods = num_periods  # Typically 6-8 per day
        self.genes = np.zeros((num_classes, num_days, num_periods), dtype=object)
        self.fitness = 0.0
        
    def get_slot(self, class_id, day, period):
        """Returns {teacher_id, subject_id, room_id} or None"""
        return self.genes[class_id][day][period]
    
    def set_slot(self, class_id, day, period, teacher_id, subject_id, room_id):
        """Assigns a lesson to a specific slot"""
        self.genes[class_id][day][period] = {
            'teacher': teacher_id,
            'subject': subject_id,
            'room': room_id
        }
```

### 1.2 Fitness Function Implementation

```python
class FitnessEvaluator:
    def __init__(self, constraints):
        self.constraints = constraints
        self.WEIGHTS = {
            'teacher_conflict': -1000,
            'room_conflict': -1000,
            'teacher_qualification': -1000,
            'max_hours_violation': -500,
            'room_capacity': -800,
            'lab_requirement': -700,
            'teacher_preference': 10,
            'minimize_gaps': 5,
            'even_distribution': 8,
            'no_consecutive_same': -3,
            'workload_balance': 7
        }
    
    def evaluate(self, chromosome):
        """Calculate total fitness score"""
        score = 0
        
        # Hard Constraints (must be 0 violations)
        score += self._check_teacher_conflicts(chromosome)
        score += self._check_room_conflicts(chromosome)
        score += self._check_teacher_qualification(chromosome)
        score += self._check_max_hours(chromosome)
        score += self._check_room_capacity(chromosome)
        score += self._check_lab_requirements(chromosome)
        
        # Soft Constraints (optimization)
        score += self._evaluate_teacher_preferences(chromosome)
        score += self._evaluate_gap_minimization(chromosome)
        score += self._evaluate_even_distribution(chromosome)
        score += self._penalize_consecutive_same(chromosome)
        score += self._evaluate_workload_balance(chromosome)
        
        chromosome.fitness = score
        return score
    
    def _check_teacher_conflicts(self, chromosome):
        """Ensure no teacher is in two places at once"""
        conflicts = 0
        for day in range(chromosome.num_days):
            for period in range(chromosome.num_periods):
                teachers_this_slot = []
                for class_idx in range(chromosome.num_classes):
                    slot = chromosome.get_slot(class_idx, day, period)
                    if slot and slot['teacher']:
                        teachers_this_slot.append(slot['teacher'])
                
                # Count duplicates
                conflicts += len(teachers_this_slot) - len(set(teachers_this_slot))
        
        return conflicts * self.WEIGHTS['teacher_conflict']
    
    def _check_room_conflicts(self, chromosome):
        """Ensure no room is double-booked"""
        conflicts = 0
        for day in range(chromosome.num_days):
            for period in range(chromosome.num_periods):
                rooms_this_slot = []
                for class_idx in range(chromosome.num_classes):
                    slot = chromosome.get_slot(class_idx, day, period)
                    if slot and slot['room']:
                        rooms_this_slot.append(slot['room'])
                
                conflicts += len(rooms_this_slot) - len(set(rooms_this_slot))
        
        return conflicts * self.WEIGHTS['room_conflict']
    
    def _evaluate_teacher_preferences(self, chromosome):
        """Reward matching teacher time preferences"""
        score = 0
        for class_idx in range(chromosome.num_classes):
            for day in range(chromosome.num_days):
                for period in range(chromosome.num_periods):
                    slot = chromosome.get_slot(class_idx, day, period)
                    if slot and slot['teacher']:
                        teacher_prefs = self.constraints.get_teacher_preferences(slot['teacher'])
                        if (day, period) in teacher_prefs.get('preferred_slots', []):
                            score += self.WEIGHTS['teacher_preference']
        return score
    
    def _evaluate_gap_minimization(self, chromosome):
        """Reward schedules with fewer gaps for teachers"""
        score = 0
        for teacher_id in self.constraints.get_all_teachers():
            for day in range(chromosome.num_days):
                slots = self._get_teacher_slots_for_day(chromosome, teacher_id, day)
                gaps = self._count_gaps(slots)
                score -= gaps * abs(self.WEIGHTS['minimize_gaps'])
        return score
    
    def _count_gaps(self, slots):
        """Count gaps in a teacher's schedule"""
        if len(slots) < 2:
            return 0
        
        sorted_slots = sorted(slots)
        gaps = 0
        for i in range(len(sorted_slots) - 1):
            gap_size = sorted_slots[i + 1] - sorted_slots[i] - 1
            if gap_size > 0:
                gaps += gap_size
        return gaps
```

### 1.3 Genetic Operators

```python
class GeneticOperators:
    @staticmethod
    def tournament_selection(population, tournament_size=5):
        """Select parent using tournament selection"""
        tournament = random.sample(population, tournament_size)
        return max(tournament, key=lambda x: x.fitness)
    
    @staticmethod
    def two_point_crossover(parent1, parent2):
        """Create offspring by combining two parents"""
        child = TimetableChromosome(
            parent1.num_classes,
            parent1.num_days,
            parent1.num_periods
        )
        
        # Select two random crossover points
        point1 = random.randint(0, parent1.num_classes // 2)
        point2 = random.randint(parent1.num_classes // 2, parent1.num_classes)
        
        for class_idx in range(parent1.num_classes):
            if point1 <= class_idx < point2:
                child.genes[class_idx] = parent1.genes[class_idx].copy()
            else:
                child.genes[class_idx] = parent2.genes[class_idx].copy()
        
        return child
    
    @staticmethod
    def swap_mutation(chromosome, mutation_rate=0.1):
        """Randomly swap two lessons"""
        if random.random() > mutation_rate:
            return chromosome
        
        # Select two random slots
        class1, day1, period1 = GeneticOperators._random_slot(chromosome)
        class2, day2, period2 = GeneticOperators._random_slot(chromosome)
        
        # Swap them
        temp = chromosome.genes[class1][day1][period1]
        chromosome.genes[class1][day1][period1] = chromosome.genes[class2][day2][period2]
        chromosome.genes[class2][day2][period2] = temp
        
        return chromosome
    
    @staticmethod
    def _random_slot(chromosome):
        """Generate random slot coordinates"""
        class_idx = random.randint(0, chromosome.num_classes - 1)
        day = random.randint(0, chromosome.num_days - 1)
        period = random.randint(0, chromosome.num_periods - 1)
        return class_idx, day, period
```

### 1.4 Main Genetic Algorithm Loop

```python
class GeneticAlgorithm:
    def __init__(self, config, constraints):
        self.config = config
        self.constraints = constraints
        self.evaluator = FitnessEvaluator(constraints)
        self.operators = GeneticOperators()
        
    def run(self, progress_callback=None):
        """Execute the genetic algorithm"""
        # Initialize population
        population = self._initialize_population()
        
        best_solution = None
        best_fitness = float('-inf')
        generations_without_improvement = 0
        
        for generation in range(self.config['max_generations']):
            # Evaluate fitness
            for individual in population:
                self.evaluator.evaluate(individual)
            
            # Track best solution
            current_best = max(population, key=lambda x: x.fitness)
            if current_best.fitness > best_fitness:
                best_fitness = current_best.fitness
                best_solution = current_best
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            
            # Check stopping criteria
            if self._is_optimal(current_best) or \
               generations_without_improvement > self.config['max_stagnation']:
                break
            
            # Report progress
            if progress_callback:
                progress_callback({
                    'generation': generation,
                    'best_fitness': best_fitness,
                    'avg_fitness': np.mean([ind.fitness for ind in population]),
                    'violations': self._count_violations(current_best)
                })
            
            # Create next generation
            population = self._evolve_population(population)
        
        return best_solution, best_fitness
    
    def _initialize_population(self):
        """Create initial random population"""
        population = []
        for _ in range(self.config['population_size']):
            individual = self._create_random_chromosome()
            population.append(individual)
        return population
    
    def _evolve_population(self, population):
        """Create next generation using genetic operators"""
        new_population = []
        
        # Elitism: Keep best individuals
        sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)
        elite_count = self.config['elitism_count']
        new_population.extend(sorted_pop[:elite_count])
        
        # Create offspring
        while len(new_population) < self.config['population_size']:
            # Selection
            parent1 = self.operators.tournament_selection(
                population, 
                self.config['tournament_size']
            )
            parent2 = self.operators.tournament_selection(
                population, 
                self.config['tournament_size']
            )
            
            # Crossover
            if random.random() < self.config['crossover_rate']:
                child = self.operators.two_point_crossover(parent1, parent2)
            else:
                child = copy.deepcopy(parent1)
            
            # Mutation
            child = self.operators.swap_mutation(child, self.config['mutation_rate'])
            
            new_population.append(child)
        
        return new_population
    
    def _is_optimal(self, chromosome):
        """Check if solution is optimal (no hard constraint violations)"""
        return self._count_violations(chromosome) == 0
    
    def _count_violations(self, chromosome):
        """Count hard constraint violations"""
        violations = 0
        # Count teacher conflicts, room conflicts, etc.
        # Implementation details...
        return violations
```

---

## 2. Database Schema - Complete SQL

```sql
-- ============================================
-- USERS & AUTHENTICATION
-- ============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    device_info JSONB,
    ip_address INET,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- MASTER DATA
-- ============================================

CREATE TABLE institutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE academic_years (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id),
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE semesters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_year_id UUID REFERENCES academic_years(id),
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    duration INTEGER DEFAULT 45, -- minutes
    type VARCHAR(50), -- lecture, lab, practical
    requires_lab BOOLEAN DEFAULT false,
    description TEXT,
    color VARCHAR(7), -- hex color for UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    institution_id UUID REFERENCES institutions(id),
    employee_id VARCHAR(50) UNIQUE,
    department VARCHAR(100),
    designation VARCHAR(100),
    max_hours_per_day INTEGER DEFAULT 6,
    max_hours_per_week INTEGER DEFAULT 30,
    preferences JSONB, -- time preferences, room preferences, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE teacher_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    proficiency_level VARCHAR(50), -- expert, proficient, basic
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(teacher_id, subject_id)
);

CREATE TABLE classrooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id),
    name VARCHAR(100) NOT NULL,
    building VARCHAR(100),
    floor INTEGER,
    capacity INTEGER NOT NULL,
    type VARCHAR(50), -- regular, lab, auditorium
    equipment JSONB, -- projector, computers, lab_equipment
    is_available BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id),
    grade VARCHAR(50) NOT NULL,
    section VARCHAR(10),
    student_count INTEGER,
    class_teacher_id UUID REFERENCES teachers(id),
    academic_year_id UUID REFERENCES academic_years(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(institution_id, grade, section, academic_year_id)
);

CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    institution_id UUID REFERENCES institutions(id),
    roll_number VARCHAR(50) UNIQUE,
    class_id UUID REFERENCES classes(id),
    date_of_birth DATE,
    guardian_name VARCHAR(255),
    guardian_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TIME SLOTS
-- ============================================

CREATE TABLE time_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    period_number INTEGER NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_break BOOLEAN DEFAULT false,
    slot_type VARCHAR(50), -- regular, lunch, recess
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(institution_id, day_of_week, period_number)
);

-- ============================================
-- TIMETABLES
-- ============================================

CREATE TABLE timetables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id),
    name VARCHAR(255) NOT NULL,
    academic_year_id UUID REFERENCES academic_years(id),
    semester_id UUID REFERENCES semesters(id),
    status VARCHAR(50) DEFAULT 'draft', -- draft, generating, generated, approved, published
    created_by UUID REFERENCES users(id),
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    published_at TIMESTAMP,
    constraints JSONB, -- hard and soft constraints
    algorithm_config JSONB, -- GA parameters used
    fitness_score FLOAT,
    generation_time INTEGER, -- seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE timetable_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timetable_id UUID REFERENCES timetables(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    teacher_id UUID REFERENCES teachers(id),
    room_id UUID REFERENCES classrooms(id),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    period_number INTEGER NOT NULL,
    start_time TIME,
    end_time TIME,
    is_locked BOOLEAN DEFAULT false, -- manually locked entries
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(timetable_id, class_id, day_of_week, period_number),
    UNIQUE(timetable_id, teacher_id, day_of_week, period_number),
    UNIQUE(timetable_id, room_id, day_of_week, period_number)
);

CREATE TABLE timetable_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timetable_id UUID REFERENCES timetables(id) ON DELETE CASCADE,
    conflict_type VARCHAR(100), -- teacher_conflict, room_conflict, etc.
    severity VARCHAR(50), -- critical, warning, info
    description TEXT,
    affected_entries UUID[], -- array of timetable_entry IDs
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    resolved_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CONSTRAINTS
-- ============================================

CREATE TABLE constraints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    institution_id UUID REFERENCES institutions(id),
    name VARCHAR(255) NOT NULL,
    constraint_type VARCHAR(50), -- hard, soft
    category VARCHAR(100), -- teacher, room, class, subject
    parameters JSONB,
    priority INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- AUDIT & LOGS
-- ============================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100), -- create, update, delete, approve, publish
    entity_type VARCHAR(100), -- timetable, teacher, class, etc.
    entity_id UUID,
    changes JSONB, -- before and after values
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- NOTIFICATIONS
-- ============================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    type VARCHAR(50), -- info, warning, success, error
    is_read BOOLEAN DEFAULT false,
    link TEXT, -- deep link to relevant page
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- User indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- Teacher indexes
CREATE INDEX idx_teachers_user_id ON teachers(user_id);
CREATE INDEX idx_teachers_institution ON teachers(institution_id);
CREATE INDEX idx_teacher_subjects_teacher ON teacher_subjects(teacher_id);
CREATE INDEX idx_teacher_subjects_subject ON teacher_subjects(subject_id);

-- Timetable indexes
CREATE INDEX idx_timetables_institution ON timetables(institution_id);
CREATE INDEX idx_timetables_status ON timetables(status);
CREATE INDEX idx_timetables_academic_year ON timetables(academic_year_id);

-- Timetable entry indexes (critical for performance)
CREATE INDEX idx_timetable_entries_timetable ON timetable_entries(timetable_id);
CREATE INDEX idx_timetable_entries_class ON timetable_entries(class_id);
CREATE INDEX idx_timetable_entries_teacher ON timetable_entries(teacher_id, day_of_week, period_number);
CREATE INDEX idx_timetable_entries_room ON timetable_entries(room_id, day_of_week, period_number);
CREATE INDEX idx_timetable_entries_day_period ON timetable_entries(day_of_week, period_number);

-- Notification indexes
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read);

-- Audit log indexes
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
```

---

## 3. API Request/Response Examples

### 3.1 Authentication

```json
// POST /api/v1/auth/login
Request:
{
  "email": "admin@school.edu",
  "password": "SecurePassword123"
}

Response:
{
  "success": true,
  "data": {
    "user": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "admin@school.edu",
      "role": "admin",
      "first_name": "John",
      "last_name": "Doe"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "dGhpc2lzYXJlZnJlc2h0b2tlbg...",
      "expires_in": 3600
    }
  }
}
```

### 3.2 Timetable Generation

```json
// POST /api/v1/timetables/:id/generate
Request:
{
  "algorithm_config": {
    "population_size": 150,
    "max_generations": 1000,
    "crossover_rate": 0.8,
    "mutation_rate": 0.1,
    "tournament_size": 5
  },
  "constraints": {
    "hard": [
      {
        "type": "no_teacher_conflict",
        "enabled": true
      },
      {
        "type": "no_room_conflict",
        "enabled": true
      },
      {
        "type": "teacher_qualification",
        "enabled": true
      }
    ],
    "soft": [
      {
        "type": "teacher_preferences",
        "weight": 10
      },
      {
        "type": "minimize_gaps",
        "weight": 5
      }
    ]
  }
}

Response:
{
  "success": true,
  "data": {
    "job_id": "gen_abc123def456",
    "status": "queued",
    "estimated_time": 120
  }
}

// GET /api/v1/timetables/:id/status
Response:
{
  "success": true,
  "data": {
    "job_id": "gen_abc123def456",
    "status": "running",
    "progress": {
      "current_generation": 450,
      "total_generations": 1000,
      "best_fitness": 875.5,
      "violations": 2,
      "elapsed_time": 60
    }
  }
}

// After completion
Response:
{
  "success": true,
  "data": {
    "job_id": "gen_abc123def456",
    "status": "completed",
    "result": {
      "timetable_id": "123e4567-e89b-12d3-a456-426614174000",
      "fitness_score": 920.8,
      "violations": 0,
      "generation_time": 118,
      "total_generations": 687,
      "alternative_solutions": [
        {
          "id": "alt_001",
          "fitness_score": 915.3
        },
        {
          "id": "alt_002",
          "fitness_score": 910.1
        }
      ]
    }
  }
}
```

### 3.3 View Schedule

```json
// GET /api/v1/schedules/teacher/:id?week=2024-W08
Response:
{
  "success": true,
  "data": {
    "teacher": {
      "id": "teacher_123",
      "name": "Dr. Smith",
      "department": "Mathematics"
    },
    "week": "2024-W08",
    "schedule": [
      {
        "day": "Monday",
        "day_of_week": 1,
        "slots": [
          {
            "period": 1,
            "start_time": "09:00",
            "end_time": "09:45",
            "subject": {
              "id": "sub_001",
              "name": "Algebra",
              "code": "MATH101"
            },
            "class": {
              "id": "class_001",
              "grade": "10",
              "section": "A"
            },
            "room": {
              "id": "room_201",
              "name": "Room 201",
              "building": "Main Block"
            }
          },
          {
            "period": 2,
            "start_time": "09:45",
            "end_time": "10:30",
            "subject": null,
            "is_break": false,
            "is_free": true
          }
        ],
        "total_hours": 6.5,
        "gaps": 1
      }
    ],
    "weekly_summary": {
      "total_hours": 28,
      "total_classes": 32,
      "total_gaps": 4,
      "subjects_taught": ["MATH101", "MATH102", "MATH201"]
    }
  }
}
```

---

## 4. Flutter State Management Architecture

### 4.1 Provider Structure

```dart
// lib/providers/timetable_provider.dart
class TimetableProvider with ChangeNotifier {
  final TimetableService _service;
  
  List<Timetable> _timetables = [];
  Timetable? _activeTimetable;
  GenerationStatus? _generationStatus;
  bool _isLoading = false;
  String? _error;
  
  List<Timetable> get timetables => _timetables;
  Timetable? get activeTimetable => _activeTimetable;
  GenerationStatus? get generationStatus => _generationStatus;
  bool get isLoading => _isLoading;
  String? get error => _error;
  
  Future<void> loadTimetables() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    
    try {
      _timetables = await _service.fetchTimetables();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<void> generateTimetable(String id, GenerationConfig config) async {
    try {
      final jobId = await _service.startGeneration(id, config);
      _pollGenerationStatus(jobId);
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }
  
  void _pollGenerationStatus(String jobId) {
    Timer.periodic(Duration(seconds: 2), (timer) async {
      try {
        _generationStatus = await _service.getGenerationStatus(jobId);
        notifyListeners();
        
        if (_generationStatus.isComplete) {
          timer.cancel();
          await loadTimetables();
        }
      } catch (e) {
        timer.cancel();
        _error = e.toString();
        notifyListeners();
      }
    });
  }
}
```

### 4.2 Widget Structure

```dart
// lib/screens/timetable/timetable_view_screen.dart
class TimetableViewScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Timetable'),
        actions: [
          IconButton(
            icon: Icon(Icons.filter_list),
            onPressed: () => _showFilterOptions(context),
          ),
          IconButton(
            icon: Icon(Icons.download),
            onPressed: () => _exportTimetable(context),
          ),
        ],
      ),
      body: Consumer<TimetableProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return Center(child: CircularProgressIndicator());
          }
          
          if (provider.error != null) {
            return ErrorWidget(message: provider.error);
          }
          
          if (provider.activeTimetable == null) {
            return EmptyState(message: 'No timetable available');
          }
          
          return TimetableGrid(timetable: provider.activeTimetable!);
        },
      ),
    );
  }
}

// lib/widgets/timetable/timetable_grid.dart
class TimetableGrid extends StatelessWidget {
  final Timetable timetable;
  
  const TimetableGrid({required this.timetable});
  
  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SingleChildScrollView(
        child: DataTable(
          columns: _buildColumns(),
          rows: _buildRows(),
        ),
      ),
    );
  }
  
  List<DataColumn> _buildColumns() {
    return [
      DataColumn(label: Text('Period')),
      DataColumn(label: Text('Monday')),
      DataColumn(label: Text('Tuesday')),
      DataColumn(label: Text('Wednesday')),
      DataColumn(label: Text('Thursday')),
      DataColumn(label: Text('Friday')),
      DataColumn(label: Text('Saturday')),
    ];
  }
  
  List<DataRow> _buildRows() {
    // Implementation details...
  }
}
```

---

## 5. Performance Optimization Strategies

### 5.1 Database Query Optimization

```python
# Use select_related and prefetch_related to minimize queries
def get_timetable_with_related(timetable_id):
    return Timetable.objects.select_related(
        'created_by',
        'approved_by',
        'academic_year',
        'semester'
    ).prefetch_related(
        'entries__class_obj',
        'entries__subject',
        'entries__teacher__user',
        'entries__room'
    ).get(id=timetable_id)

# Use database-level aggregation
from django.db.models import Count, Avg

def get_teacher_statistics(teacher_id):
    return TimetableEntry.objects.filter(
        teacher_id=teacher_id
    ).aggregate(
        total_classes=Count('id'),
        avg_classes_per_day=Avg('entries_per_day')
    )
```

### 5.2 Caching Strategy

```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

# Cache published timetables (they don't change often)
def get_published_timetable(timetable_id):
    cache_key = f'timetable_{timetable_id}'
    timetable = cache.get(cache_key)
    
    if timetable is None:
        timetable = Timetable.objects.get(id=timetable_id)
        cache.set(cache_key, timetable, timeout=3600)  # 1 hour
    
    return timetable

# Cache schedules
@cache_page(60 * 15)  # 15 minutes
def teacher_schedule_view(request, teacher_id):
    # View implementation
    pass
```

### 5.3 Async Task Processing

```python
# celery_tasks.py
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def generate_timetable_task(self, timetable_id, config):
    try:
        timetable = Timetable.objects.get(id=timetable_id)
        timetable.status = 'generating'
        timetable.save()
        
        # Run genetic algorithm
        ga = GeneticAlgorithm(config, constraints)
        
        # Progress callback
        def progress_callback(progress_data):
            cache.set(f'gen_progress_{timetable_id}', progress_data)
        
        best_solution, fitness = ga.run(progress_callback)
        
        # Save results
        save_timetable_solution(timetable, best_solution)
        
        timetable.status = 'generated'
        timetable.fitness_score = fitness
        timetable.save()
        
        return {'status': 'success', 'timetable_id': str(timetable_id)}
        
    except Exception as e:
        timetable.status = 'failed'
        timetable.save()
        raise self.retry(exc=e, countdown=60)
```

---

This technical specification provides detailed implementation guidance for the Smart Timetable Generator project.
