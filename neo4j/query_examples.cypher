// 1. Query all paths from role A to role B, ordered by step count.
MATCH path = (start:Job {name: $from_job})-[:TRANSFER_TO|VERTICAL_TO*1..5]->(end:Job {name: $to_job})
WHERE all(node IN nodes(path) WHERE single(other IN nodes(path) WHERE other = node))
RETURN [node IN nodes(path) | node.name] AS jobs,
       length(path) AS steps,
       reduce(score = 1.0, rel IN relationships(path) | score * coalesce(rel.success_rate, 0.5)) AS cumulative_success_rate
ORDER BY steps ASC, cumulative_success_rate DESC;

// 2. Query paths a student can walk right now.
MATCH path = (start:Job {name: $from_job})-[:TRANSFER_TO|VERTICAL_TO*1..5]->(end:Job {name: $to_job})
WHERE all(node IN nodes(path) WHERE single(other IN nodes(path) WHERE other = node))
WITH path, relationships(path) AS rels
WITH path,
     reduce(required = [], rel IN rels | required + coalesce(rel.required_skills, [])) AS required_skills
WHERE all(skill IN required_skills WHERE skill IN $student_skills)
RETURN [node IN nodes(path) | node.name] AS jobs,
       required_skills,
       length(path) AS steps
ORDER BY steps ASC;

// 3. Query path success rate, time cost and difficulty.
MATCH path = (start:Job {name: $from_job})-[:TRANSFER_TO|VERTICAL_TO*1..5]->(end:Job {name: $to_job})
WHERE all(node IN nodes(path) WHERE single(other IN nodes(path) WHERE other = node))
RETURN [rel IN relationships(path) | {
  source: startNode(rel).name,
  target: endNode(rel).name,
  relation_type: type(rel),
  success_rate: rel.success_rate,
  time_cost: rel.time_cost,
  difficulty: rel.difficulty
}] AS edge_chain;

// 4. Query all missing skills along a path.
MATCH path = (start:Job {name: $from_job})-[:TRANSFER_TO|VERTICAL_TO*1..5]->(end:Job {name: $to_job})
WHERE all(node IN nodes(path) WHERE single(other IN nodes(path) WHERE other = node))
WITH relationships(path) AS rels
RETURN reduce(skills = [], rel IN rels | skills + coalesce(rel.required_skills, [])) AS required_skills;
