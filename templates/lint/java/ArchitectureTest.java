// src/test/java/<패키지>/ArchitectureTest.java로 복사합니다.
// 의존성: testImplementation 'com.tngtech.archunit:archunit-junit5:<최신 버전>'
// 계층 방향(controller → service → repo)을 어기면 ./gradlew test가 실패합니다.
// 기능별 패키지(domain/<기능>/controller, service, repo, entity, dto) 구조를 기준으로 합니다.
package com.example.app;

import static com.tngtech.archunit.library.Architectures.layeredArchitecture;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

@AnalyzeClasses(packages = "com.example.app", importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureTest {

    @ArchTest
    static final ArchRule 계층_방향을_지킨다 =
            layeredArchitecture()
                    .consideringOnlyDependenciesInLayers()
                    .layer("Controller").definedBy("..controller..")
                    .layer("Service").definedBy("..service..")
                    .layer("Repository").definedBy("..repo..", "..repository..")
                    .whereLayer("Controller").mayNotBeAccessedByAnyLayer()
                    .whereLayer("Service").mayOnlyBeAccessedByLayers("Controller")
                    .whereLayer("Repository").mayOnlyBeAccessedByLayers("Service");

    @ArchTest
    static final ArchRule 엔티티는_웹_계층과_DTO를_모른다 =
            noClasses()
                    .that().resideInAPackage("..entity..")
                    .should().dependOnClassesThat().resideInAnyPackage("..controller..", "..dto..");
}
