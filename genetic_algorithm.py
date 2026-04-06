import random
import numpy as np
from collections import defaultdict
from app import db, Subject, Teacher, Classroom, Class, TimetableEntry

class TimetableChromosome:
    """Represents a complete timetable solution"""
    def __init__(self, num_classes, num_days=5, num_periods=8):
        self.num_classes = num_classes
        self.num_days = num_days
        self.num_periods = num_periods
        self.genes = {}  # Dict structure: {(class_id, day, period): {teacher, subject, room}}
        self.fitness = 0.0
    
    def set_slot(self, class_id, day, period, teacher_id, subject_id, room_id):
        self.genes[(class_id, day, period)] = {
            'teacher': teacher_id,
            'subject': subject_id,
            'room': room_id
        }
    
    def get_slot(self, class_id, day, period):
        return self.genes.get((class_id, day, period))

class FitnessEvaluator:
    """Evaluates fitness of timetable solutions"""
    WEIGHTS = {
        'teacher_conflict': -1000,
        'room_conflict': -1000,
        'teacher_qualification': -1000,
        'max_hours_violation': -500,
        'teacher_preference': 10,
        'minimize_gaps': 5,
        'even_distribution': 8,
    }
    
    def __init__(self):
        self.teachers = {t.id: t for t in Teacher.query.all()}
        self.subjects = {s.id: s for s in Subject.query.all()}
        self.rooms = {r.id: r for r in Classroom.query.all()}
    
    def evaluate(self, chromosome):
        """Calculate total fitness score"""
        score = 0
        score += self._check_teacher_conflicts(chromosome)
        score += self._check_room_conflicts(chromosome)
        score += self._evaluate_gap_minimization(chromosome)
        score += self._evaluate_even_distribution(chromosome)
        
        chromosome.fitness = score
        return score
    
    def _check_teacher_conflicts(self, chromosome):
        """Ensure no teacher is in two places at once"""
        conflicts = 0
        for day in range(chromosome.num_days):
            for period in range(chromosome.num_periods):
                teachers_this_slot = []
                for class_id in range(1, chromosome.num_classes + 1):
                    slot = chromosome.get_slot(class_id, day, period)
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
                for class_id in range(1, chromosome.num_classes + 1):
                    slot = chromosome.get_slot(class_id, day, period)
                    if slot and slot['room']:
                        rooms_this_slot.append(slot['room'])
                
                conflicts += len(rooms_this_slot) - len(set(rooms_this_slot))
        
        return conflicts * self.WEIGHTS['room_conflict']
    
    def _evaluate_gap_minimization(self, chromosome):
        """Reward schedules with fewer gaps for teachers"""
        score = 0
        for teacher_id in self.teachers.keys():
            for day in range(chromosome.num_days):
                slots = self._get_teacher_slots_for_day(chromosome, teacher_id, day)
                gaps = self._count_gaps(slots)
                score -= gaps * abs(self.WEIGHTS['minimize_gaps'])
        return score
    
    def _get_teacher_slots_for_day(self, chromosome, teacher_id, day):
        """Get all periods where teacher is scheduled on a day"""
        slots = []
        for period in range(chromosome.num_periods):
            for class_id in range(1, chromosome.num_classes + 1):
                slot = chromosome.get_slot(class_id, day, period)
                if slot and slot['teacher'] == teacher_id:
                    slots.append(period)
                    break
        return sorted(slots)
    
    def _count_gaps(self, slots):
        """Count gaps in a teacher's schedule"""
        if len(slots) < 2:
            return 0
        
        gaps = 0
        for i in range(len(slots) - 1):
            gap_size = slots[i + 1] - slots[i] - 1
            if gap_size > 0:
                gaps += gap_size
        return gaps
    
    def _evaluate_even_distribution(self, chromosome):
        """Reward even distribution of subjects across days"""
        score = 0
        for class_id in range(1, chromosome.num_classes + 1):
            subject_counts = defaultdict(lambda: defaultdict(int))
            for day in range(chromosome.num_days):
                for period in range(chromosome.num_periods):
                    slot = chromosome.get_slot(class_id, day, period)
                    if slot and slot['subject']:
                        subject_counts[slot['subject']][day] += 1
            
            # Penalize if same subject appears multiple times on same day
            for subject_id, day_counts in subject_counts.items():
                for day, count in day_counts.items():
                    if count > 1:
                        score -= (count - 1) * 5
        
        return score

class GeneticOperators:
    """Genetic operators for evolution"""
    
    @staticmethod
    def tournament_selection(population, tournament_size=5):
        """Select parent using tournament selection"""
        tournament = random.sample(population, min(tournament_size, len(population)))
        return max(tournament, key=lambda x: x.fitness)
    
    @staticmethod
    def two_point_crossover(parent1, parent2):
        """Create offspring by combining two parents"""
        child = TimetableChromosome(parent1.num_classes, parent1.num_days, parent1.num_periods)
        
        # Get all genes
        all_keys = list(set(parent1.genes.keys()) | set(parent2.genes.keys()))
        
        # Split point
        split = len(all_keys) // 2
        random.shuffle(all_keys)
        
        for i, key in enumerate(all_keys):
            if i < split and key in parent1.genes:
                child.genes[key] = parent1.genes[key].copy()
            elif key in parent2.genes:
                child.genes[key] = parent2.genes[key].copy()
        
        return child
    
    @staticmethod
    def swap_mutation(chromosome, mutation_rate=0.1):
        """Randomly swap two lessons"""
        if random.random() > mutation_rate or not chromosome.genes:
            return chromosome
        
        keys = list(chromosome.genes.keys())
        if len(keys) < 2:
            return chromosome
        
        # Select two random slots
        key1, key2 = random.sample(keys, 2)
        
        # Swap them
        chromosome.genes[key1], chromosome.genes[key2] = chromosome.genes[key2], chromosome.genes[key1]
        
        return chromosome

class GeneticAlgorithm:
    """Main genetic algorithm for timetable generation"""
    
    def __init__(self, timetable_id, config=None):
        self.timetable_id = timetable_id
        self.config = config or {
            'population_size': 50,
            'max_generations': 200,
            'crossover_rate': 0.8,
            'mutation_rate': 0.15,
            'tournament_size': 5,
            'elitism_count': 3,
            'max_stagnation': 30
        }
        
        # Load data
        self.classes = Class.query.all()
        self.subjects = Subject.query.all()
        self.teachers = Teacher.query.all()
        self.rooms = Classroom.query.all()
        
        self.evaluator = FitnessEvaluator()
        self.operators = GeneticOperators()
    
    def run(self):
        """Execute the genetic algorithm"""
        print("Starting timetable generation...")
        
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
                print(f"Generation {generation}: New best fitness = {best_fitness:.2f}")
            else:
                generations_without_improvement += 1
            
            # Check stopping criteria
            if generations_without_improvement > self.config['max_stagnation']:
                print(f"Converged after {generation} generations")
                break
            
            # Create next generation
            population = self._evolve_population(population)
        
        # Save best solution to database
        self._save_to_database(best_solution)
        
        print(f"Timetable generation complete! Final fitness: {best_fitness:.2f}")
        return {'fitness': best_fitness, 'generations': generation}
    
    def _initialize_population(self):
        """Create initial random population"""
        population = []
        for _ in range(self.config['population_size']):
            individual = self._create_random_chromosome()
            population.append(individual)
        return population
    
    def _create_random_chromosome(self):
        """Create a random valid timetable"""
        chromosome = TimetableChromosome(len(self.classes), num_days=5, num_periods=8)
        
        # For each class, assign subjects randomly
        for class_idx, class_obj in enumerate(self.classes, start=1):
            # Calculate how many periods to fill (e.g., 30 periods per week)
            periods_to_fill = min(30, 5 * 8)  # 5 days, 8 periods max
            
            slots = []
            for day in range(5):
                for period in range(8):
                    slots.append((day, period))
            
            random.shuffle(slots)
            
            # Assign subjects
            for i in range(min(periods_to_fill, len(slots))):
                day, period = slots[i]
                
                if self.subjects and self.teachers and self.rooms:
                    subject = random.choice(self.subjects)
                    teacher = random.choice(self.teachers)
                    room = random.choice(self.rooms)
                    
                    chromosome.set_slot(class_idx, day, period, teacher.id, subject.id, room.id)
        
        return chromosome
    
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
            parent1 = self.operators.tournament_selection(population, self.config['tournament_size'])
            parent2 = self.operators.tournament_selection(population, self.config['tournament_size'])
            
            # Crossover
            if random.random() < self.config['crossover_rate']:
                child = self.operators.two_point_crossover(parent1, parent2)
            else:
                child = TimetableChromosome(parent1.num_classes, parent1.num_days, parent1.num_periods)
                child.genes = parent1.genes.copy()
            
            # Mutation
            child = self.operators.swap_mutation(child, self.config['mutation_rate'])
            
            new_population.append(child)
        
        return new_population
    
    def _save_to_database(self, chromosome):
        """Save the best solution to database"""
        # Delete existing entries
        TimetableEntry.query.filter_by(timetable_id=self.timetable_id).delete()
        
        # Time slots mapping
        time_slots = [
            ("08:00", "08:45"), ("08:45", "09:30"), ("09:30", "10:15"),
            ("10:30", "11:15"), ("11:15", "12:00"), ("12:00", "12:45"),
            ("13:30", "14:15"), ("14:15", "15:00")
        ]
        
        # Save new entries
        for (class_id, day, period), slot_data in chromosome.genes.items():
            if slot_data:
                start_time, end_time = time_slots[period] if period < len(time_slots) else ("00:00", "00:45")
                
                entry = TimetableEntry(
                    timetable_id=self.timetable_id,
                    class_id=class_id,
                    subject_id=slot_data['subject'],
                    teacher_id=slot_data['teacher'],
                    room_id=slot_data['room'],
                    day_of_week=day,
                    period_number=period,
                    start_time=start_time,
                    end_time=end_time
                )
                db.session.add(entry)
        
        db.session.commit()
